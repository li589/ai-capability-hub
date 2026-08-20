# -*- coding: utf-8 -*-
"""
机器学习预测模型
ML-based Stock Prediction

基于 LightGBM / RandomForest 的股价方向预测。
专为 A 股市场设计，特征工程包含技术面 + 资金面 + 情绪面。

特征列表：
- 技术面: MA偏离度、RSI、MACD、布林带位置、KDJ、成交量比
- 动量面: 5/10/20/60日涨跌幅
- 波动面: 历史波动率、ATR
- 资金面: 主力资金流向、换手率变化
- 市场面: 指数相关性、板块强度

使用示例：
```python
from quantitative.ml_predictor import MLPredictor

predictor = MLPredictor()
predictor.train(features, labels)
prediction = predictor.predict(features_new)
```
"""

import math
import warnings
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False


def ml_available() -> bool:
    """v8.0: sklearn + numpy 齐全才启用 ML overlay。
    测试环境（conftest 屏蔽 numpy/sklearn）下返回 False，主链路自动降级到规则引擎。"""
    return HAS_SKLEARN


@dataclass
class MLPrediction:
    """ML 预测结果"""
    symbol: str
    direction: str             # "上涨" / "下跌" / "震荡"
    prob_up: float             # 上涨概率
    prob_down: float           # 下跌概率
    confidence: float          # 预测置信度
    model_name: str            # 使用的模型
    features_used: List[str]   # 使用的特征
    feature_importance: Dict[str, float] = field(default_factory=dict)


class FeatureEngineer:
    """
    A股特征工程

    从原始 OHLCV 数据中提取 ML 特征。
    """

    @staticmethod
    def _safe_float(v, default=0.0) -> float:
        try:
            return float(v)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def calc_rsi(prices: List[float], period: int = 14) -> float:
        """计算 RSI"""
        if len(prices) < period + 1:
            return 50.0
        gains = []
        losses = []
        for i in range(1, period + 1):
            diff = prices[-i] - prices[-i - 1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - 100 / (1 + rs)

    @staticmethod
    def calc_macd(prices: List[float]) -> Tuple[float, float]:
        """计算 MACD (DIF, Histogram)

        DIF = EMA(12) - EMA(26)
        DEA = EMA(DIF, 9)  — 对 DIF 序列取 EMA（修复：原实现返回 dif*0.2 的伪 DEA）
        Hist = DIF - DEA
        """
        if len(prices) < 26:
            return 0.0, 0.0

        def ema_series(data, n):
            k = 2.0 / (n + 1)
            out = [data[0]]
            for v in data[1:]:
                out.append(v * k + out[-1] * (1 - k))
            return out

        ema12 = ema_series(prices, 12)
        ema26 = ema_series(prices, 26)
        dif_series = [f - s for f, s in zip(ema12, ema26)]
        dea = ema_series(dif_series, 9)[-1]
        dif = dif_series[-1]
        return dif, dif - dea

    @staticmethod
    def extract_features(
        ohlcv_list: List[Dict],
        money_flow: Dict = None,
    ) -> Dict[str, float]:
        """
        从 OHLCV 数据提取特征

        Args:
            ohlcv_list: [{"open":, "high":, "low":, "close":, "volume":}, ...]
            money_flow: 资金流向数据

        Returns:
            Dict: 特征字典
        """
        if len(ohlcv_list) < 60:
            return {}

        closes = [d.get("close", 0) for d in ohlcv_list]
        highs = [d.get("high", 0) for d in ohlcv_list]
        lows = [d.get("low", 0) for d in ohlcv_list]
        volumes = [d.get("volume", 0) for d in ohlcv_list]
        current = closes[-1]

        features = {}

        # ── 均线偏离度 ──
        for period in [5, 10, 20, 60]:
            if len(closes) >= period:
                ma = sum(closes[-period:]) / period
                features[f"ma{period}_dev"] = (current - ma) / ma * 100

        # ── 动量特征 ──
        for period in [1, 3, 5, 10, 20, 60]:
            if len(closes) > period:
                features[f"ret_{period}d"] = (
                    (closes[-1] - closes[-(period + 1)]) / closes[-(period + 1)] * 100
                )

        # ── RSI ──
        features["rsi_6"] = FeatureEngineer.calc_rsi(closes, 6)
        features["rsi_14"] = FeatureEngineer.calc_rsi(closes, 14)
        features["rsi_24"] = FeatureEngineer.calc_rsi(closes, 24)

        # ── MACD ──
        dif, hist = FeatureEngineer.calc_macd(closes)
        features["macd_dif"] = dif
        features["macd_hist"] = hist

        # ── 布林带位置 ──
        if len(closes) >= 20:
            recent = closes[-20:]
            ma20 = sum(recent) / 20
            std20 = math.sqrt(sum((c - ma20) ** 2 for c in recent) / 20)
            upper = ma20 + 2 * std20
            lower = ma20 - 2 * std20
            features["bb_position"] = (
                (current - lower) / (upper - lower) if upper != lower else 0.5
            )
            features["bb_width"] = (upper - lower) / ma20 * 100 if ma20 > 0 else 0

        # ── 波动率 ──
        if len(closes) >= 20:
            returns = []
            for i in range(1, len(closes)):
                if closes[i - 1] > 0:
                    returns.append((closes[i] - closes[i - 1]) / closes[i - 1])
            if returns:
                features["vol_20d"] = np.std(returns[-20:]) * math.sqrt(252) * 100

        # ── ATR ──
        if len(highs) >= 14:
            tr_list = []
            for i in range(-14, 0):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1]),
                )
                tr_list.append(tr)
            features["atr_14"] = sum(tr_list) / 14
            features["atr_pct"] = features["atr_14"] / current * 100 if current > 0 else 0

        # ── 成交量特征 ──
        if len(volumes) >= 20:
            avg_vol_5 = sum(volumes[-5:]) / 5
            avg_vol_20 = sum(volumes[-20:]) / 20
            features["vol_ratio_5"] = volumes[-1] / avg_vol_5 if avg_vol_5 > 0 else 1
            features["vol_ratio_20"] = volumes[-1] / avg_vol_20 if avg_vol_20 > 0 else 1
            # 量价配合
            features["vol_price_corr"] = np.corrcoef(
                volumes[-20:], closes[-20:]
            )[0, 1] if len(volumes) >= 20 else 0

        # ── KDJ ──
        if len(highs) >= 9:
            h9 = max(highs[-9:])
            l9 = min(lows[-9:])
            rsv = (current - l9) / (h9 - l9) * 100 if h9 != l9 else 50
            features["kdj_k"] = 2 / 3 * 50 + 1 / 3 * rsv

        # ── 资金面 ──
        if money_flow:
            features["main_flow"] = money_flow.get("main_net", 0)
            features["flow_ratio"] = money_flow.get("flow_ratio", 0)

        # ── 日内特征 ──
        if current > 0:
            day_high = highs[-1]
            day_low = lows[-1]
            day_open = ohlcv_list[-1].get("open", closes[-1])
            features["amplitude"] = (day_high - day_low) / current * 100
            features["upper_shadow"] = (day_high - max(closes[-1], day_open)) / current * 100
            features["lower_shadow"] = (min(closes[-1], day_open) - day_low) / current * 100

        return features

    @staticmethod
    def feature_names() -> List[str]:
        """返回所有特征名称"""
        return [
            "ma5_dev", "ma10_dev", "ma20_dev", "ma60_dev",
            "ret_1d", "ret_3d", "ret_5d", "ret_10d", "ret_20d", "ret_60d",
            "rsi_6", "rsi_14", "rsi_24",
            "macd_dif", "macd_hist",
            "bb_position", "bb_width",
            "vol_20d", "atr_14", "atr_pct",
            "vol_ratio_5", "vol_ratio_20", "vol_price_corr",
            "kdj_k", "amplitude", "upper_shadow", "lower_shadow",
            "main_flow", "flow_ratio",
        ]


class MLPredictor:
    """
    机器学习预测器

    支持 RandomForest（默认）和 LightGBM（可选）。
    预测未来 N 日的涨跌方向。

    参数：
    - model_type: "randomforest" | "lightgbm" | "ensemble"
    - prediction_horizon: 预测天数
    - threshold: 涨跌分类阈值（收益率 > threshold% 为"上涨"）
    """

    def __init__(
        self,
        model_type: str = "randomforest",
        prediction_horizon: int = 5,
        threshold: float = 0.5,
    ):
        if not HAS_SKLEARN:
            raise ImportError(
                "scikit-learn 未安装。请运行: pip install scikit-learn"
            )

        self.model_type = model_type
        self.prediction_horizon = prediction_horizon
        self.threshold = threshold
        self._model = None
        self._scaler = StandardScaler()
        self._trained = False
        self._feature_names: List[str] = []
        self._feature_importance: Dict[str, float] = {}

    def _create_model(self):
        """创建模型实例"""
        if self.model_type == "lightgbm":
            if not HAS_LIGHTGBM:
                raise ImportError(
                    "LightGBM 未安装。请运行: pip install lightgbm"
                )
            return lgb.LGBMClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                num_leaves=31,
                min_child_samples=20,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbose=-1,
            )
        elif self.model_type == "ensemble":
            # 简单集成：RF + LGBM
            self._rf_model = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1,
            )
            if HAS_LIGHTGBM:
                self._lgb_model = lgb.LGBMClassifier(
                    n_estimators=150,
                    max_depth=5,
                    learning_rate=0.05,
                    random_state=42,
                    verbose=-1,
                )
            return self._rf_model  # 返回 RF 作为默认
        else:
            return RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1,
            )

    def prepare_labels(
        self, prices: List[float], horizon: int = None
    ) -> np.ndarray:
        """
        准备标签：未来 N 日涨跌方向

        Returns:
            np.ndarray: 0=下跌, 1=震荡, 2=上涨，长度为 len(prices)-horizon
            （尾部 horizon 个样本没有未来数据，已截断，
              修复：原实现将其保留并错误标记为 0=下跌，污染训练集）
        """
        horizon = horizon or self.prediction_horizon
        n = len(prices)
        labels = np.zeros(max(0, n - horizon), dtype=int)

        for i in range(n - horizon):
            future_ret = (prices[i + horizon] - prices[i]) / prices[i] * 100
            if future_ret > self.threshold:
                labels[i] = 2  # 上涨
            elif future_ret < -self.threshold:
                labels[i] = 0  # 下跌
            else:
                labels[i] = 1  # 震荡

        return labels

    def train(
        self,
        features_list: List[Dict[str, float]],
        labels: np.ndarray,
        validation_split: float = 0.2,
    ) -> Dict:
        """
        训练模型

        Args:
            features_list: 特征字典列表
            labels: 标签数组
            validation_split: 验证集比例

        Returns:
            Dict: 训练结果指标
        """
        if not features_list:
            raise ValueError("特征列表为空")

        # 提取特征矩阵
        self._feature_names = list(features_list[0].keys())
        X = np.array([
            [f.get(name, 0) for name in self._feature_names]
            for f in features_list
        ], dtype=float)

        # 处理 NaN/Inf
        X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)

        # 标准化
        X = self._scaler.fit_transform(X)

        # 对齐标签
        min_len = min(len(X), len(labels))
        X = X[:min_len]
        y = labels[:min_len]

        # 划分训练/验证集
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, shuffle=False
        )

        # 创建并训练模型
        self._model = self._create_model()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._model.fit(X_train, y_train)

        # ensemble 模式：LGBM 也需训练（修复：原实现只 fit RF，
        # predict 时调用未训练的 LGBM 会抛 NotFittedError）
        if self.model_type == "ensemble" and getattr(self, "_lgb_model", None) is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._lgb_model.fit(X_train, y_train)

        # 验证
        y_pred = self._model.predict(X_val)
        accuracy = accuracy_score(y_val, y_pred)

        # 特征重要性
        if hasattr(self._model, "feature_importances_"):
            importances = self._model.feature_importances_
            self._feature_importance = {
                name: round(imp, 4)
                for name, imp in zip(self._feature_names, importances)
            }
            # 排序
            self._feature_importance = dict(
                sorted(
                    self._feature_importance.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:15]
            )

        self._trained = True

        return {
            "accuracy": round(accuracy, 4),
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "top_features": list(self._feature_importance.keys())[:5],
        }

    def predict(self, features: Dict[str, float]) -> MLPrediction:
        """
        预测单只股票的涨跌方向

        Args:
            features: 特征字典

        Returns:
            MLPrediction: 预测结果
        """
        if not self._trained:
            raise RuntimeError("模型尚未训练，请先调用 train()")

        # 提取特征
        X = np.array([
            features.get(name, 0) for name in self._feature_names
        ], dtype=float).reshape(1, -1)
        X = np.nan_to_num(X, nan=0.0)
        X = self._scaler.transform(X)

        # 预测
        if self.model_type == "ensemble" and hasattr(self, "_lgb_model"):
            prob_rf = self._rf_model.predict_proba(X)[0]
            prob_lgb = self._lgb_model.predict_proba(X)[0]
            prob = (prob_rf + prob_lgb) / 2
        else:
            prob = self._model.predict_proba(X)[0]

        # prob 对应 [下跌, 震荡, 上涨]
        prob_down = prob[0] if len(prob) > 0 else 0.33
        prob_flat = prob[1] if len(prob) > 1 else 0.34
        prob_up = prob[2] if len(prob) > 2 else 0.33

        max_prob = max(prob_down, prob_flat, prob_up)
        if max_prob == prob_up:
            direction = "上涨"
            confidence = prob_up
        elif max_prob == prob_down:
            direction = "下跌"
            confidence = prob_down
        else:
            direction = "震荡"
            confidence = prob_flat

        return MLPrediction(
            symbol="",
            direction=direction,
            prob_up=round(prob_up, 4),
            prob_down=round(prob_down, 4),
            confidence=round(confidence, 4),
            model_name=self.model_type,
            features_used=self._feature_names[:10],
            feature_importance=self._feature_importance,
        )

    def predict_direction(
        self, ohlcv_list: List[Dict], money_flow: Dict = None
    ) -> Dict:
        """
        从原始 OHLCV 数据直接预测方向

        Args:
            ohlcv_list: OHLCV 数据列表
            money_flow: 资金流向数据

        Returns:
            Dict: 预测结果
        """
        # 提取特征
        features = FeatureEngineer.extract_features(ohlcv_list, money_flow)
        if not features:
            return {"direction": "数据不足", "confidence": 0}

        # 预测
        result = self.predict(features)

        return {
            "direction": result.direction,
            "prob_up": result.prob_up,
            "prob_down": result.prob_down,
            "confidence": result.confidence,
            "horizon_days": self.prediction_horizon,
            "model": result.model_name,
            "top_features": list(result.feature_importance.keys())[:5],
        }


def demo():
    """演示 ML 预测（滑动窗口特征 + 自身时序标签，按日期对齐）"""
    np.random.seed(42)

    n_paths = 8        # 模拟 8 只股票
    n_days = 260
    horizon = 5

    print("生成模拟训练数据（每只股票滑动窗口，标签来自其自身未来收益）...")
    features_list = []
    labels_list = []
    predictor = MLPredictor(prediction_horizon=horizon)
    latest_features = None

    for _ in range(n_paths):
        prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, n_days)))
        ohlcv = [
            {
                "open": p * (1 + np.random.normal(0, 0.005)),
                "high": p * (1 + abs(np.random.normal(0, 0.01))),
                "low": p * (1 - abs(np.random.normal(0, 0.01))),
                "close": p,
                "volume": np.random.uniform(1e6, 1e8),
            }
            for p in prices
        ]
        closes = [d["close"] for d in ohlcv]
        # 该股自身时序标签（尾部 horizon 天已截断）
        stock_labels = predictor.prepare_labels(closes, horizon)
        # 滑动窗口特征，与标签按日期对齐
        for i in range(59, len(ohlcv) - horizon):
            features = FeatureEngineer.extract_features(ohlcv[i - 59: i + 1])
            if features:
                features_list.append(features)
                labels_list.append(int(stock_labels[i]))
        latest_features = FeatureEngineer.extract_features(ohlcv[-60:])

    # 训练
    print(f"训练模型中...（{len(features_list)} 个样本）")
    labels = np.array(labels_list, dtype=int)
    result = predictor.train(features_list, labels)
    print(f"训练完成: 准确率={result['accuracy']:.2%}")
    print(f"Top 5 特征: {result['top_features']}")

    # 预测最新一天
    if latest_features:
        prediction = predictor.predict(latest_features)
        print(f"\n最新预测: 方向={prediction.direction}, 置信度={prediction.confidence:.2%}")


if __name__ == "__main__":
    demo()


# ============================================================
# v3.1.0 增量 — 时序交叉验证 / 概率校准 / 置信区间 / 扩展特征
# ============================================================

try:
    from sklearn.model_selection import TimeSeriesSplit
    HAS_TSCV = True
except ImportError:
    HAS_TSCV = False

try:
    from sklearn.calibration import CalibratedClassifierCV
    HAS_CALIBRATION = True
except ImportError:
    HAS_CALIBRATION = False


class FeatureEngineerV2(FeatureEngineer):
    """特征工程 v2 — 28 维特征（基线 27 + 1 个量价背离度）。"""

    @staticmethod
    def extract_features(ohlcv_list, money_flow=None):
        base = FeatureEngineer.extract_features(ohlcv_list, money_flow)
        if not base:
            return base
        closes = [d.get('close', 0) for d in ohlcv_list]
        volumes = [d.get('volume', 0) for d in ohlcv_list]
        if len(closes) >= 20 and len(volumes) >= 20:
            try:
                import numpy as _np
                ret = _np.diff(closes[-20:]) / closes[-20:][:-1]
                vol_norm = _np.array(volumes[-20:], dtype=float)
                vol_norm = (vol_norm - vol_norm.mean()) / (vol_norm.std() + 1e-9)
                base['vp_divergence'] = float(_np.corrcoef(ret, vol_norm)[0, 1])
            except Exception:
                base['vp_divergence'] = 0.0
        else:
            base['vp_divergence'] = 0.0
        return base

    @staticmethod
    def feature_names():
        names = FeatureEngineer.feature_names()
        names.append('vp_divergence')
        return names


def train_with_time_cv(features_list, labels, n_splits=5,
                       model_type='randomforest', random_state=42):
    """时序交叉验证训练 — 严格按时间顺序切分，避免未来信息泄露。

    Returns:
        dict 含 accuracy_mean / accuracy_std / per_fold / trained_model / scaler /
        feature_names / feature_importance
    """
    if not HAS_SKLEARN:
        raise RuntimeError('scikit-learn 未安装')
    if not features_list:
        raise ValueError('特征列表为空')

    feature_names = list(features_list[0].keys())
    X = np.array([[f.get(name, 0) for name in feature_names]
                  for f in features_list], dtype=float)
    X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
    y = np.array(labels)
    min_len = min(len(X), len(y))
    X, y = X[:min_len], y[:min_len]

    if HAS_TSCV and len(X) >= n_splits * 30:
        cv = TimeSeriesSplit(n_splits=n_splits)
        splitter = cv.split(X)
    else:
        # Fallback: 简单滚动划分，避免越界
        folds = []
        chunk = max(1, len(X) // (n_splits + 1))
        for k in range(n_splits):
            train_end = chunk * (k + 2)
            val_end = min(train_end + chunk, len(X))
            tr = np.arange(0, train_end - chunk)
            vr = np.arange(train_end, val_end)
            if len(tr) >= 30 and len(vr) >= 1:
                folds.append((tr, vr))
        splitter = iter(folds)

    scaler = StandardScaler()
    accuracies = []
    fold_metrics = []
    last_model = None
    importance_acc = None

    for fold_idx, (tr, va) in enumerate(splitter):
        scaler_fold = StandardScaler().fit(X[tr])
        Xtr = scaler_fold.transform(X[tr])
        Xva = scaler_fold.transform(X[va])
        if model_type == 'lightgbm' and HAS_LIGHTGBM:
            m = lgb.LGBMClassifier(n_estimators=200, max_depth=5, learning_rate=0.05,
                                   num_leaves=31, random_state=random_state, verbose=-1)
        else:
            m = RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_split=10,
                                       min_samples_leaf=5, random_state=random_state, n_jobs=-1)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            m.fit(Xtr, y[tr])
        yhat = m.predict(Xva)
        acc = float(accuracy_score(y[va], yhat))
        accuracies.append(acc)
        fold_metrics.append({'fold': fold_idx, 'accuracy': acc,
                             'train_size': int(len(tr)), 'val_size': int(len(va))})
        last_model = m
        if hasattr(m, 'feature_importances_'):
            imp = m.feature_importances_
            importance_acc = imp if importance_acc is None else importance_acc + imp

    # 最终模型用全部数据再训练一次（保留最新 scaler）
    scaler_final = StandardScaler().fit(X)
    Xall = scaler_final.transform(X)
    if model_type == 'lightgbm' and HAS_LIGHTGBM:
        final = lgb.LGBMClassifier(n_estimators=200, max_depth=5, learning_rate=0.05,
                                   num_leaves=31, random_state=random_state, verbose=-1)
    else:
        final = RandomForestClassifier(n_estimators=200, max_depth=10,
                                       min_samples_split=10, min_samples_leaf=5,
                                       random_state=random_state, n_jobs=-1)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        final.fit(Xall, y)
    last_model = final
    scaler = scaler_final

    importance = {}
    if importance_acc is not None and hasattr(final, 'feature_importances_'):
        for n, v in zip(feature_names, final.feature_importances_):
            importance[n] = round(float(v), 4)
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:15])

    arr = np.array(accuracies) if accuracies else np.array([0.0])
    return {
        'accuracy_mean': float(arr.mean()),
        'accuracy_std': float(arr.std()),
        'per_fold': fold_metrics,
        'trained_model': last_model,
        'scaler': scaler,
        'feature_names': feature_names,
        'feature_importance': importance,
        'model_type': model_type,
    }


def calibrate_model(model, X_val, y_val, method='sigmoid'):
    """概率校准 — Platt (sigmoid) 或 Isotonic。

    Returns:
        CalibratedClassifierCV 包装后的分类器。
    """
    if not HAS_CALIBRATION:
        raise RuntimeError('scikit-learn 未安装，无法校准')
    base = CalibratedClassifierCV(model, method=method, cv='prefit')
    base.fit(X_val, y_val)
    return base


def predict_with_confidence(model, scaler, feature_names, raw_features,
                             n_estimators_bootstrap=20):
    """单样本预测 + 置信区间。

    通过对 RF 子采样得到 20 次预测概率，计算均值与 95% 区间。

    Returns:
        dict: direction, prob_up, prob_down, prob_flat, ci_low, ci_high,
              confidence, model
    """
    X = np.array([[raw_features.get(name, 0) for name in feature_names]],
                 dtype=float)
    X = np.nan_to_num(X, nan=0.0)
    Xs = scaler.transform(X)

    # 主预测
    proba = model.predict_proba(Xs)[0]
    n_cls = len(proba)
    proba_pad = list(proba) + [0.0] * (3 - n_cls)
    prob_down, prob_flat, prob_up = proba_pad[0], proba_pad[1], proba_pad[2]

    # 子采样置信区间
    pis = []
    try:
        from sklearn.ensemble import RandomForestClassifier
        if isinstance(model, RandomForestClassifier):
            estimators = model.estimators_
            for _ in range(min(n_estimators_bootstrap, len(estimators))):
                idx = np.random.choice(len(estimators),
                                       size=max(1, len(estimators) // 2),
                                       replace=False)
                probs = np.mean([estimators[i].predict_proba(Xs)[0] for i in idx],
                                axis=0)
                pis.append(probs)
    except Exception:
        pass

    if pis:
        pis = np.array(pis)
        up_vals = pis[:, 2] if pis.shape[1] >= 3 else pis[:, -1]
        ci_low = float(np.percentile(up_vals, 2.5))
        ci_high = float(np.percentile(up_vals, 97.5))
        prob_up = float(up_vals.mean())
    else:
        ci_low, ci_high = prob_up, prob_up

    prob_max = max(prob_up, prob_down, prob_flat)
    if prob_max == prob_up:
        direction = '上涨'
    elif prob_max == prob_down:
        direction = '下跌'
    else:
        direction = '震荡'

    return {
        'direction': direction,
        'prob_up': round(prob_up, 4),
        'prob_down': round(prob_down, 4),
        'prob_flat': round(prob_flat, 4),
        'ci_low': round(ci_low, 4),
        'ci_high': round(ci_high, 4),
        'confidence': round(float(prob_max), 4),
        'model': type(model).__name__,
    }


# ============================================================
# v4.0.0 新增 — 多周期 ML 预测器 (MultiHorizonMLPredictor)
# ============================================================

import numpy as _np


class MultiHorizonMLPredictor:
    """多周期机器学习预测器 (v4.0.0)

    为每个预测周期(1d/3d/5d/1M/1Q)分别训练一个 RF/LightGBM 模型，
    使用 FeatureEngineerV2(28 维特征) + train_with_time_cv(时序CV) +
    calibrate_model(概率校准)，输出统一多周期预测。

    使用示例:
        mhp = MultiHorizonMLPredictor(model_type='randomforest')
        results = mhp.train_and_predict(ohlcv_history, money_flow)
        for horizon, pred in results.items():
            print(f'{horizon}: {pred["direction"]} conf={pred["confidence"]:.2%}')
    """

    HORIZONS = {"1d": 1, "3d": 3, "5d": 5, "1M": 22, "1Q": 66}

    def __init__(self, model_type: str = "randomforest", n_splits: int = 5):
        self.model_type = model_type
        self.n_splits = n_splits
        self._models: Dict[str, Dict] = {}  # {horizon: {trained_model, scaler, feature_names, importance}}

    def train_and_predict(
        self, ohlcv_list: List[Dict], money_flow: Dict = None
    ) -> Dict[str, Dict]:
        """对每个周期训练并预测。

        Args:
            ohlcv_list: OHLCV 历史数据 [{open,high,low,close,volume}, ...], 需≥60条
            money_flow: 资金流向 Dict(可选)

        Returns:
            Dict[str, Dict]: {horizon: {direction, prob_up, prob_down, prob_flat,
                                        ci_low, ci_high, confidence, top_features}}
        """
        if len(ohlcv_list) < 60:
            return {"error": f"数据不足(需要≥60条，当前{len(ohlcv_list)}条)"}

        # 1. 提取特征（28维）
        features = FeatureEngineerV2.extract_features(ohlcv_list, money_flow)
        if not features:
            return {"error": "特征提取失败"}

        # 2. 逐条生成多条样本（滑动窗口）
        feature_names = list(features.keys())
        all_features = []
        all_prices = []
        for i in range(60, len(ohlcv_list)):
            window = ohlcv_list[i - 60:i]
            f = FeatureEngineerV2.extract_features(window, money_flow)
            if f:
                all_features.append([f.get(name, 0) for name in feature_names])
                all_prices.append(window[-1].get("close", 0))

        if len(all_features) < 50:
            return {"error": f"有效样本不足(需要≥50，当前{len(all_features)}条)"}

        X = _np.array(all_features, dtype=float)
        X = _np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
        prices = all_prices

        # 3. 对每个周期训练+预测
        results = {}

        for horizon_name, horizon_days in self.HORIZONS.items():
            try:
                # 生成标签
                mlp = MLPredictor(
                    model_type=self.model_type,
                    prediction_horizon=horizon_days,
                    threshold=0.5,
                )
                labels = mlp.prepare_labels(prices, horizon=horizon_days)

                # 时序交叉验证训练
                train_res = train_with_time_cv(
                    [dict(zip(feature_names, row)) for row in X],
                    labels,
                    n_splits=self.n_splits,
                    model_type=self.model_type,
                )
                accuracy = train_res.get("accuracy_mean", 0.5)

                if accuracy < 0.2 or accuracy is None:
                    # 模型无效，跳过
                    results[horizon_name] = {
                        "direction": "数据不足",
                        "confidence": 0.0,
                        "accuracy": accuracy,
                        "note": "模型准确率过低，跳过",
                    }
                    continue

                # 保存模型
                self._models[horizon_name] = {
                    "trained_model": train_res["trained_model"],
                    "scaler": train_res["scaler"],
                    "feature_names": train_res["feature_names"],
                    "feature_importance": train_res.get("feature_importance", {}),
                }

                # 对最新样本预测
                latest_features = dict(zip(feature_names, X[-1]))
                pred = predict_with_confidence(
                    train_res["trained_model"],
                    train_res["scaler"],
                    train_res["feature_names"],
                    latest_features,
                )

                # 提取Top特征
                top_f = sorted(
                    train_res.get("feature_importance", {}).items(),
                    key=lambda x: x[1], reverse=True
                )[:5]

                results[horizon_name] = {
                    "direction": pred["direction"],
                    "prob_up": pred["prob_up"],
                    "prob_down": pred["prob_down"],
                    "prob_flat": pred["prob_flat"],
                    "ci_low": pred["ci_low"],
                    "ci_high": pred["ci_high"],
                    "confidence": pred["confidence"],
                    "accuracy": round(accuracy, 4),
                    "top_features": [{"name": n, "importance": round(v, 4)} for n, v in top_f],
                    "model_type": self.model_type,
                }
            except Exception as e:
                results[horizon_name] = {
                    "direction": "error",
                    "confidence": 0.0,
                    "note": f"{type(e).__name__}: {e}",
                }

        return results

    def get_trained_horizons(self) -> List[str]:
        """返回已有训练模型的周期"""
        return list(self._models.keys())
