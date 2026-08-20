const fs = require('fs');
const path = require('path');
const axios = require('axios');

const SKILL_NAME = 'gaode-map-lbs';
const APP_NAME = 'gaode-map-lbs';
const PUBLIC_AMAP_WEBSERVICE_KEY = 'f0f99d37a1379881c4d77d45d98b05a6';
const USER_REGION_MAINLAND = 'mainland_china_incl_hk_mo_tw';
const USER_REGION_NON_MAINLAND = 'non_mainland_excl_hk_mo_tw';
const API_PROFILES = {
  [USER_REGION_MAINLAND]: {
    label: '中国大陆（含港澳台）',
    baseUrl: 'https://restapi.amap.com',
    endpoints: {
      placeText: '/v5/place/text',
      walking: '/v3/direction/walking',
      driving: '/v3/direction/driving',
      riding: '/v4/direction/bicycling',
      transit: '/v3/direction/transit/integrated',
    },
  },
  [USER_REGION_NON_MAINLAND]: {
    label: '非中国大陆（不含港澳台）',
    baseUrl: 'https://sg-restapi.opnavi.com',
    endpoints: {
      placeText: '/v3/place/text',
      walking: '/v3/direction/walking',
      driving: '/v3/direction/driving',
      riding: null,
      transit: null,
    },
  },
};

// 配置文件路径
const CONFIG_FILE = path.join(__dirname, 'config.json');

/**
 * 读取配置文件
 */
function readConfig() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const data = fs.readFileSync(CONFIG_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('读取配置文件失败:', error.message);
  }
  return {};
}

/**
 * 保存配置文件
 */
function saveConfig(config) {
  try {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2), 'utf8');
    // 设置文件权限为仅所有者可读写，防止密钥泄露
    fs.chmodSync(CONFIG_FILE, 0o600);
    console.log('配置已保存到:', CONFIG_FILE);
    return true;
  } catch (error) {
    console.error('保存配置文件失败:', error.message);
    return false;
  }
}

/**
 * 获取高德 Web Service Key
 */
function getWebServiceKey() {
  const config = readConfig();
  return config.webServiceKey || null;
}

function getOverseasWebServiceKey() {
  const config = readConfig();
  return config.overseasWebServiceKey || null;
}

function normalizeUserRegion(value) {
  const raw = String(value || process.env.AMAP_USER_REGION || '').trim().toLowerCase();
  if (
    raw === USER_REGION_NON_MAINLAND ||
    raw === 'non-mainland' ||
    raw === 'non_mainland' ||
    raw === 'overseas' ||
    raw === 'abroad' ||
    raw === 'global' ||
    raw === '非中国大陆' ||
    raw === '海外'
  ) {
    return USER_REGION_NON_MAINLAND;
  }
  return USER_REGION_MAINLAND;
}

function getApiProfile(params = {}) {
  const userRegion = normalizeUserRegion(params.userRegion);
  return {
    userRegion,
    ...API_PROFILES[userRegion],
  };
}

function buildApiUrl(profile, endpointName) {
  const endpoint = profile.endpoints[endpointName];
  if (!endpoint) {
    throw new Error(`${profile.label} 暂未配置 ${endpointName} 对应的海外 Web API endpoint`);
  }
  return `${profile.baseUrl}${endpoint}`;
}

/**
 * 设置高德 Web Service Key
 */
function setWebServiceKey(key) {
  const config = readConfig();
  config.webServiceKey = key;
  return saveConfig(config);
}

/**
 * 检查并提示用户输入 Key
 */
async function ensureWebServiceKey(userRegion = USER_REGION_MAINLAND) {
  if (userRegion === USER_REGION_NON_MAINLAND) {
    let overseasKey = process.env.AMAP_OVERSEAS_WEBSERVICE_KEY;

    if (!overseasKey) {
      overseasKey = getOverseasWebServiceKey();
    }

    if (!overseasKey) {
      overseasKey = process.env.AMAP_WEBSERVICE_KEY || getWebServiceKey();
    }

    if (!overseasKey) {
      console.warn('\nℹ️  未找到自有海外高德 Web Service Key，已使用官方公共测试 Key。');
      console.warn('公共 Key 每天有免费额度，先到先得；额度用完后请访问 https://mapsplatform.opnavi.com/ 提交 Contact Sales 表单获取专属支持。\n');
      overseasKey = PUBLIC_AMAP_WEBSERVICE_KEY;
    }

    return overseasKey;
  }

  // 优先从环境变量读取
  let key = process.env.AMAP_WEBSERVICE_KEY;
  
  if (!key && process.env.AMAP_KEY) {
    key = process.env.AMAP_KEY;
    console.warn('⚠️  环境变量 AMAP_KEY 已废弃，请迁移到 AMAP_WEBSERVICE_KEY');
  }
  
  if (!key) {
    // 尝试从配置文件读取
    key = getWebServiceKey();
  }
  
  if (!key) {
    console.warn('\nℹ️  未找到自有高德 Web Service Key，已使用官方公共测试 Key。');
    console.warn('公共 Key 每天有免费额度，先到先得；额度用完后请到 https://lbs.amap.com/ 注册并创建自有 Key。\n');
    key = PUBLIC_AMAP_WEBSERVICE_KEY;
  }
  
  return key;
}

/**
 * POI 搜索
 * @param {Object} params - 搜索参数
 * @param {string} params.keywords - 查询关键字
 * @param {string} params.city - 城市名称或城市编码
 * @param {string} params.types - POI类型编码
 * @param {string} params.location - 中心点坐标
 * @param {number} params.radius - 搜索半径(米)
 * @param {number} params.page - 当前页数
 * @param {number} params.offset - 每页记录数
 */
async function searchPOI(params) {
  const profile = getApiProfile(params);
  const key = await ensureWebServiceKey(profile.userRegion);
  
  const url = buildApiUrl(profile, 'placeText');
  
  const requestParams = {
    key: key,
    appname: APP_NAME,
    keywords: params.keywords || '',
    ...params,
  };

  delete requestParams.userRegion;

  if (profile.userRegion === USER_REGION_NON_MAINLAND) {
    requestParams.city = params.city || params.adcode || '';
  } else {
    requestParams.region = params.city || '';
    requestParams.city_limit = params.cityLimit !== false;
  }
  
  try {
    console.log('🔍 正在搜索 POI...');
    const response = await axios.get(url, { params: requestParams });
    
    if (response.data.status === '1') {
      console.log(`✅ 搜索成功，共找到 ${response.data.count} 条结果\n`);
      return response.data;
    } else {
      console.error('❌ 搜索失败:', response.data.info);
      return null;
    }
  } catch (error) {
    console.error('❌ 请求失败:', error.message);
    return null;
  }
}

/**
 * 步行路径规划
 * @param {Object} params - 规划参数
 * @param {string} params.origin - 起点坐标 "经度,纬度"
 * @param {string} params.destination - 终点坐标 "经度,纬度"
 */
async function walkingRoute(params) {
  const profile = getApiProfile(params);
  const key = await ensureWebServiceKey(profile.userRegion);
  
  const url = buildApiUrl(profile, 'walking');
  
  const requestParams = {
    key: key,
    appname: APP_NAME,
    origin: params.origin,
    destination: params.destination
  };
  
  try {
    console.log('🚶 正在规划步行路线...');
    const response = await axios.get(url, { params: requestParams });
    
    if (response.data.status === '1') {
      console.log('✅ 步行路线规划成功\n');
      return response.data;
    } else {
      console.error('❌ 步行路线规划失败:', response.data.info);
      return null;
    }
  } catch (error) {
    console.error('❌ 请求失败:', error.message);
    return null;
  }
}

/**
 * 驾车路径规划
 * @param {Object} params - 规划参数
 * @param {string} params.origin - 起点坐标 "经度,纬度"
 * @param {string} params.destination - 终点坐标 "经度,纬度"
 * @param {string} params.waypoints - 途经点坐标，多个用;分隔
 * @param {number} params.strategy - 驾车策略，默认10
 */
async function drivingRoute(params) {
  const profile = getApiProfile(params);
  const key = await ensureWebServiceKey(profile.userRegion);
  
  const url = buildApiUrl(profile, 'driving');
  
  const requestParams = {
    key: key,
    appname: APP_NAME,
    origin: params.origin,
    destination: params.destination,
    strategy: params.strategy || 10,
    extensions: 'base'
  };
  
  if (params.waypoints) {
    requestParams.waypoints = params.waypoints;
  }
  
  try {
    console.log('🚗 正在规划驾车路线...');
    const response = await axios.get(url, { params: requestParams });
    
    if (response.data.status === '1') {
      console.log('✅ 驾车路线规划成功\n');
      return response.data;
    } else {
      console.error('❌ 驾车路线规划失败:', response.data.info);
      return null;
    }
  } catch (error) {
    console.error('❌ 请求失败:', error.message);
    return null;
  }
}

/**
 * 骑行路径规划
 * @param {Object} params - 规划参数
 * @param {string} params.origin - 起点坐标 "经度,纬度"
 * @param {string} params.destination - 终点坐标 "经度,纬度"
 */
async function ridingRoute(params) {
  const profile = getApiProfile(params);
  const key = await ensureWebServiceKey(profile.userRegion);
  
  const url = buildApiUrl(profile, 'riding');
  
  const requestParams = {
    key: key,
    appname: APP_NAME,
    origin: params.origin,
    destination: params.destination
  };
  
  try {
    console.log('🚴 正在规划骑行路线...');
    const response = await axios.get(url, { params: requestParams });
    
    if (response.data.errcode === 0) {
      console.log('✅ 骑行路线规划成功\n');
      return response.data;
    } else {
      console.error('❌ 骑行路线规划失败:', response.data.errmsg);
      return null;
    }
  } catch (error) {
    console.error('❌ 请求失败:', error.message);
    return null;
  }
}

/**
 * 公交路径规划
 * @param {Object} params - 规划参数
 * @param {string} params.origin - 起点坐标 "经度,纬度"
 * @param {string} params.destination - 终点坐标 "经度,纬度"
 * @param {string} params.city - 城市名称或城市编码
 * @param {number} params.strategy - 公交策略，默认0（最快捷）
 * @param {boolean} params.nightflag - 是否计算夜班车，默认false
 */
async function transitRoute(params) {
  const profile = getApiProfile(params);
  const key = await ensureWebServiceKey(profile.userRegion);
  
  const url = buildApiUrl(profile, 'transit');
  
  const requestParams = {
    key: key,
    appname: APP_NAME,
    origin: params.origin,
    destination: params.destination,
    city: params.city,
    strategy: params.strategy || 0,
    nightflag: params.nightflag ? 1 : 0
  };
  
  try {
    console.log('🚌 正在规划公交路线...');
    const response = await axios.get(url, { params: requestParams });
    
    if (response.data.status === '1') {
      console.log('✅ 公交路线规划成功\n');
      return response.data;
    } else {
      console.error('❌ 公交路线规划失败:', response.data.info);
      return null;
    }
  } catch (error) {
    console.error('❌ 请求失败:', error.message);
    return null;
  }
}

/**
 * 生成地图可视化链接
 * @param {Array} mapTaskData - 地图任务数据数组
 * @returns {string} 可视化链接
 */
function generateMapLink(mapTaskData) {
  const baseUrl = 'https://a.amap.com/jsapi_demo_show/static/openclaw/travel_plan.html';
  const dataStr = encodeURIComponent(JSON.stringify(mapTaskData));
  return `${baseUrl}?data=${dataStr}&appname=${encodeURIComponent(APP_NAME)}`;
}

/**
 * 旅游规划助手
 * @param {Object} params - 规划参数
 * @param {string} params.city - 城市名称
 * @param {Array<string>} params.interests - 兴趣点关键词数组，如 ['景点', '美食', '酒店']
 * @param {string} params.routeType - 路线类型：driving/walking/riding/transfer
 * @returns {Object} 包含 pois、mapTaskData、mapLink 和 htmlLink
 */
async function travelPlanner(params) {
  const { city, interests = [], routeType = 'walking', userRegion } = params;
  
  console.log(`\n🗺️  开始为您规划 ${city} 的旅游行程...\n`);
  
  const mapTaskData = [];
  const poiResults = [];
  
  // 搜索各类兴趣点
  for (const interest of interests) {
    console.log(`📍 搜索 ${interest}...`);
    const result = await searchPOI({
      keywords: interest,
      city: city,
      page: 1,
      offset: 5,
      userRegion,
    });
    
    if (result && result.pois && result.pois.length > 0) {
      poiResults.push(...result.pois);
      
      // 添加到地图数据 - 严格按照 PoiTask 接口格式
      result.pois.forEach(poi => {
        const [lng, lat] = poi.location.split(',').map(Number);
        mapTaskData.push({
          type: 'poi',
          lnglat: [lng, lat],
          sort: poi.type || interest,
          text: poi.name,
          remark: poi.address || `${interest}推荐`
        });
      });
    }
  }
  
  // 如果有多个POI，规划路线
  if (poiResults.length >= 2) {
    console.log(`\n🛣️  规划游览路线（${routeType}）...\n`);
    
    for (let i = 0; i < poiResults.length - 1; i++) {
      const start = poiResults[i];
      const end = poiResults[i + 1];
      
      const [startLng, startLat] = start.location.split(',').map(Number);
      const [endLng, endLat] = end.location.split(',').map(Number);
      
      // 添加路线到地图数据 - 严格按照 RouteTask 接口格式
      const routeTask = {
        type: 'route',
        routeType: routeType,
        start: [startLng, startLat],
        end: [endLng, endLat],
        remark: `从 ${start.name} 到 ${end.name}`
      };
      
      // 如果是公交路线，添加 city 参数
      if (routeType === 'transfer') {
        routeTask.city = city;
      }
      
      mapTaskData.push(routeTask);
    }
  }
  
  
  console.log('\n✅ 旅游规划完成！\n');
  console.log('📍 推荐地点：');
  poiResults.forEach((poi, index) => {
    console.log(`${index + 1}. ${poi.name}`);
    console.log(`   地址: ${poi.address}`);
    console.log(`   类型: ${poi.type}\n`);
  });
  
  return {
    pois: poiResults,
    mapTaskData,
    mapLink: generateMapLink(mapTaskData),
  };
}

// 导出函数供其他脚本使用
module.exports = {
  readConfig,
  saveConfig,
  getWebServiceKey,
  getOverseasWebServiceKey,
  setWebServiceKey,
  ensureWebServiceKey,
  SKILL_NAME,
  APP_NAME,
  PUBLIC_AMAP_WEBSERVICE_KEY,
  USER_REGION_MAINLAND,
  USER_REGION_NON_MAINLAND,
  getApiProfile,
  searchPOI,
  walkingRoute,
  drivingRoute,
  ridingRoute,
  transitRoute,
  generateMapLink,
  travelPlanner
};

// 如果直接运行此文件，执行示例搜索
if (require.main === module) {
  (async () => {
    try {
      // 示例：搜索北京的肯德基
      const result = await searchPOI({
        keywords: '肯德基',
        city: '北京',
        page: 1,
        offset: 10
      });
      
      if (result && result.pois) {
        console.log('搜索结果:');
        result.pois.forEach((poi, index) => {
          console.log(`${index + 1}. ${poi.name}`);
          console.log(`   地址: ${poi.address}`);
          console.log(`   类型: ${poi.type}`);
          console.log(`   坐标: ${poi.location}\n`);
        });
      }
    } catch (error) {
      console.error('执行失败:', error.message);
      process.exit(1);
    }
  })();
}
