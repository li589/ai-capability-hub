#!/usr/bin/env node

/**
 * 同程程心大模型 - 旅游搜索 API 查询脚本
 * 
 * 用法：
 *   node query.js "北京到上海的火车票" Train
 *   node query.js "明天飞广州的机票" Flight
 *   node query.js "上海外滩附近的酒店" Hotel
 * 
 * 配置（优先级：环境变量 > config.json）：
 *   - CHENGXIN_API_KEY（环境变量）
 *   - 或创建 config.json 文件（见 config.example.json）
 */

const https = require('https');
const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');

// 接口配置
const API_URL = 'https://wx.17u.cn/skills/gateway/api/v1/gateway/resource';

// 版本号
const API_VERSION = '0.2.0';

// 配置读取（优先级：环境变量 > config.json）
let API_KEY = process.env.CHENGXIN_API_KEY;

/**
 * 构建 Authorization Token
 * 格式：Bearer <apiKey>
 * 直接使用用户配置的完整 apiKey，不做任何修改
 * @param {string} key - 用户配置的 API Key
 * @returns {string} - 完整的 Token
 */
function build_auth_token(key) {
  if (!key) return '';
  return `Bearer ${key}`;
}

if (!API_KEY) {
  try {
    const config_path = path.join(__dirname, '..', 'config.json');
    const config = JSON.parse(fs.readFileSync(config_path, 'utf8'));
    API_KEY = config.apiKey;
  } catch (e) {
    console.error('❌ 配置错误：未找到 CHENGXIN_API_KEY 环境变量或 config.json 文件');
    console.error('   请设置环境变量或在技能目录下创建 config.json 文件');
    process.exit(1);
  }
}

// planning 枚举映射
const PLANNING_MAP = {
  '机票': 'Flight',
  '航班': 'Flight',
  '飞机': 'Flight',
  'flight': 'Flight',
  '火车': 'Train',
  '高铁': 'Train',
  '动车': 'Train',
  '车票': 'Train',
  'train': 'Train',
  '酒店': 'Hotel',
  '住宿': 'Hotel',
  '宾馆': 'Hotel',
  'hotel': 'Hotel',
  '景区': 'Scenery',
  '景点': 'Scenery',
  '门票': 'Scenery',
  'scenery': 'Scenery',
  '度假': 'Travel',
  '旅游': 'Travel',
  'travel': 'Travel'
};

/**
 * 自动识别意图
 * @param {string} query - 用户查询
 * @returns {string} - planning 枚举值
 */
function detect_planning(query) {
  const lower_query = query.toLowerCase();
  
  for (const [keyword, planning] of Object.entries(PLANNING_MAP)) {
    if (lower_query.includes(keyword.toLowerCase())) {
      return planning;
    }
  }
  
  // 默认返回 Travel（旅行）
  return 'Travel';
}

/**
 * 调用程心 API
 * @param {string} query - 用户查询
 * @param {string} planning - 意图类型
 * @param {string} channel - 通信渠道
 * @param {string} surface - 交互界面
 * @returns {Promise<object>} - API 响应
 */
function query_chengxin(query, planning, channel = '', surface = '') {
  return new Promise((resolve, reject) => {
    const parsed_url = url.parse(API_URL);
    const is_https = parsed_url.protocol === 'https:';
    const client = is_https ? https : http;
    
    const post_data = JSON.stringify({
      query: query,
      planning: planning,
      channel: channel,
      surface: surface,
      version: API_VERSION
    });
    
    const options = {
      hostname: parsed_url.hostname,
      port: parsed_url.port || (is_https ? 443 : 80),
      path: parsed_url.path,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(post_data),
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://www.ly.com',
        'Referer': 'https://www.ly.com/',
        'Authorization': build_auth_token(API_KEY)
      }
    };
    
    const req = client.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          resolve(result);
        } catch (e) {
          reject(new Error(`解析响应失败：${e.message}`));
        }
      });
    });
    
    req.on('error', (e) => {
      reject(new Error(`请求失败：${e.message}`));
    });
    
    req.write(post_data);
    req.end();
  });
}

/**
 * 格式化火车票结果
 * @param {object} train_data - 火车数据
 * @param {boolean} use_table - 是否使用表格格式（默认 false=卡片）
 * @param {boolean} use_plain_link - 是否使用纯文本链接（默认 false=Markdown 链接）
 * @returns {string} - 格式化输出
 */
function format_train_result(train_data, use_table = false, use_plain_link = false) {
  if (!train_data || !train_data.trainList) {
    return '未找到相关火车票信息';
  }
  
  const trains = train_data.trainList;
  let output = '🚄 火车票查询结果：\n\n';
  
  if (use_table) {
    // 表格格式
    output += '| 车次 | 出发站 | 到达站 | 出发时间 | 到达时间 | 运行时长 | 最低价 | 余票 | PC 预订 | 手机预订 |\n';
    output += '|------|--------|--------|---------|---------|---------|--------|------|--------|---------|\n';
    
    trains.forEach((train) => {
      const train_no = train.trainType === 'GD' ? `🚅 ${train.trainNo}` : `🚆 ${train.trainNo}`;
      const dep_station = train.depStationName || '-';
      const arr_station = train.arrStationName || '-';
      const dep_time = train.depTime || '-';
      const arr_time = train.arrTime || '-';
      const run_time = train.runTime || '-';
      const price = train.price ? `¥${train.price}` : '暂无价格';
      
      let ticket_info = '查询中';
      if (train.ticketList && train.ticketList.length > 0) {
        const available_tickets = train.ticketList.filter(t => parseInt(t.ticketLeft) > 0);
        if (available_tickets.length > 0) {
          ticket_info = available_tickets.map(t => `${t.ticketType}(${t.ticketLeft})`).join(', ');
        } else {
          ticket_info = '售罄';
        }
      }
      
      const pc_link = train.pcRedirectUrl || train.clawRedirectUrl || train.redirectUrl || '#';
      const mobile_link = train.clawRedirectUrl || train.redirectUrl || '#';
      
      let pc_link_md, mobile_link_md;
      if (use_plain_link) {
        pc_link_md = pc_link !== '#' ? pc_link : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? mobile_link : '暂不可用';
      } else {
        pc_link_md = pc_link !== '#' ? `[PC 端](${pc_link})` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `[手机端](${mobile_link})` : '暂不可用';
      }
      
      output += `| ${train_no} | ${dep_station} | ${arr_station} | ${dep_time} | ${arr_time} | ${run_time} | ${price} | ${ticket_info} | ${pc_link_md} | ${mobile_link_md} |\n`;
    });
  } else {
    // 卡片格式
    trains.forEach((train) => {
      const train_no = train.trainType === 'GD' ? `🚅 ${train.trainNo}` : `🚆 ${train.trainNo}`;
      const dep_station = train.depStationName || '-';
      const arr_station = train.arrStationName || '-';
      const dep_time = train.depTime || '-';
      const arr_time = train.arrTime || '-';
      const run_time = train.runTime || '-';
      const price = train.price ? `¥${train.price}` : '暂无价格';
      
      let ticket_info = '';
      if (train.ticketList && train.ticketList.length > 0) {
        const available_tickets = train.ticketList.filter(t => parseInt(t.ticketLeft) > 0);
        if (available_tickets.length > 0) {
          ticket_info = available_tickets.map(t => `${t.ticketType}(${t.ticketLeft})`).join(', ');
        } else {
          ticket_info = '售罄';
        }
      }
      
      const pc_link = train.pcRedirectUrl || train.clawRedirectUrl || train.redirectUrl || '#';
      const mobile_link = train.clawRedirectUrl || train.redirectUrl || '#';
      
      let pc_link_md, mobile_link_md;
      if (use_plain_link) {
        pc_link_md = pc_link !== '#' ? `PC 端：${pc_link}` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `手机端：${mobile_link}` : '暂不可用';
      } else {
        pc_link_md = pc_link !== '#' ? `[PC 端](${pc_link})` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `[手机端](${mobile_link})` : '暂不可用';
      }
      
      output += `### ${train_no} | ${dep_station} → ${arr_station}\n`;
      output += `**出发时间** ${dep_time} | **到达时间** ${arr_time} | **时长** ${run_time}\n`;
      output += `**最低价** ${price}\n`;
      output += `**余票** ${ticket_info}\n`;
      output += `**预订** ${pc_link_md} | ${mobile_link_md}\n`;
      output += '\n---\n\n';
    });
  }
  
  output += '💡 **更多选择**：也可以打开 **同程旅行 APP** 或在 **微信 - 我 - 服务** 中，点击 **火车票机票** 以及 **酒店民宿** 查看更丰富的资源。\n';
  output += '\n';
  return output;
}

/**
 * 格式化机票结果（卡片式列表）
 * @param {object} flight_data - 机票数据
 * @param {boolean} use_table - 是否使用表格格式
 * @param {boolean} use_plain_link - 是否使用纯文本链接（微信渠道）
 * @returns {string} - 格式化输出
 */
function format_flight_result(flight_data, use_table = false, use_plain_link = false) {
  if (!flight_data || !flight_data.flightList) {
    return '未找到相关机票信息';
  }
  
  const flights = flight_data.flightList.slice(0, 5);
  // 获取顶层 PC 链接（列表页）作为备选
  const page_pc_link = flight_data.pageDataList?.[0]?.pcRedirectUrl || '';
  
  // 检测是否为特价机票场景（字段为 null 表示特价推荐）
  const is_special_price = flights.length > 0 && (flights[0].flightNo === null || flights[0].flightNo === undefined);
  
  let output = '✈️ 机票查询结果：\n\n';
  
  if (is_special_price && use_table) {
    // 特价机票格式：表格
    output += '| 目的地 | 价格 | 日期 | 折扣 | 原价 | 预订链接 |\n';
    output += '|--------|------|------|------|------|----------|\n';
    
    flights.forEach((flight) => {
      const dep_name = flight.depName || '-';
      const arr_name = flight.arrName || '-';
      const price = flight.price ? `¥${flight.price}` : '暂无价格';
      const week = flight.week || '-';
      const discount = flight.discount || '-';
      const origin_price = flight.originPrice ? `¥${flight.originPrice}` : '-';
      const pc_link = flight.clawRedirectUrl || flight.redirectUrl || '#';
      const mobile_link = flight.clawRedirectUrl || flight.redirectUrl || '#';
      
      let pc_link_md, mobile_link_md;
      if (use_plain_link) {
        pc_link_md = pc_link !== '#' ? `PC 端：${pc_link}` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `手机端：${mobile_link}` : '暂不可用';
      } else {
        pc_link_md = pc_link !== '#' ? `[PC 端](${pc_link})` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `[手机端](${mobile_link})` : '暂不可用';
      }
      
      output += `| ${dep_name}→${arr_name} | ${price} | ${week} | ${discount} | ${origin_price} | ${pc_link_md} \\| ${mobile_link_md} |\n`;
    });
  } else {
    // 常规航班格式：卡片
    flights.forEach((flight) => {
      const flight_no = flight.flightNo || '-';
      const airline = flight.airlineName || '-';
      const dep_airport = flight.depAirportName || '-';
      const arr_airport = flight.arrAirportName || '-';
      const dep_time = flight.depTime || '-';
      const arr_time = flight.arrTime || '-';
      const run_time = flight.runTime || '-';
      const price = flight.price ? `¥${flight.price}` : '暂无价格';
      
      // 构建链接 - 航班对象没有 pcRedirectUrl，使用顶层列表页链接
      const pc_link = page_pc_link || flight.clawRedirectUrl || flight.redirectUrl || '#';
      const mobile_link = flight.clawRedirectUrl || flight.redirectUrl || '#';
      
      let pc_link_md, mobile_link_md;
      if (use_plain_link) {
        pc_link_md = pc_link !== '#' ? `PC 端：${pc_link}` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `手机端：${mobile_link}` : '暂不可用';
      } else {
        pc_link_md = pc_link !== '#' ? `[PC 端](${pc_link})` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `[手机端](${mobile_link})` : '暂不可用';
      }
      
      output += `### ✈️ ${flight_no} | ${dep_airport} → ${arr_airport}\n`;
      output += `**出发时间** ${dep_time} | **到达时间** ${arr_time} | **时长** ${run_time}\n`;
      output += `**价格** ${price}\n`;
      output += `**航司** ${airline}\n`;
      output += `**预订** ${pc_link_md} | ${mobile_link_md}\n`;
      output += '\n---\n\n';
    });
  }
  
  output += '💡 **更多选择**：也可以打开 **同程旅行 APP** 或在 **微信 - 我 - 服务** 中，点击 **火车票机票** 以及 **酒店民宿** 查看更丰富的资源。\n';
  output += '\n';
  return output;
}

/**
 * 格式化酒店结果（卡片式列表）
 * @param {object} hotel_data - 酒店数据
 * @param {boolean} use_table - 是否使用表格格式
 * @param {boolean} use_plain_link - 是否使用纯文本链接（微信渠道）
 * @returns {string} - 格式化输出
 */
function format_hotel_result(hotel_data, use_table = false, use_plain_link = false) {
  if (!hotel_data || !hotel_data.hotelList) {
    return '未找到相关酒店信息';
  }
  
  const hotels = hotel_data.hotelList.slice(0, 5);
  let output = '🏨 酒店查询结果：\n\n';
  
  if (use_table) {
    // 表格格式
    output += '| 酒店名称 | 价格 | 类型 | 评分 | 地址 | PC 预订 | 手机预订 |\n';
    output += '|----------|------|------|------|------|--------|---------|\n';
    
    hotels.forEach((hotel) => {
      const name = hotel.name || '未知酒店';
      const price = hotel.price ? `¥${hotel.price}` : '暂无价格';
      const star = hotel.star || '未评级';
      const score = hotel.score || '暂无';
      const comment_num = hotel.commentNum || '0';
      const address = hotel.address || '';
      const resource_id = hotel.resourceId || '';
      
      // 构建链接 - PC 详情页使用酒店 ID 构建
      let pc_link = '#';
      if (resource_id) {
        const raw_pc_link = hotel.pcRedirectUrl || '';
        if (raw_pc_link.includes('hoteldetail')) {
          pc_link = raw_pc_link;
        } else if (raw_pc_link.includes('hotellist')) {
          const in_date_match = raw_pc_link.match(/inDate=([^&]+)/);
          const out_date_match = raw_pc_link.match(/outDate=([^&]+)/);
          const in_date = in_date_match ? in_date_match[1] : '2026-03-29';
          const out_date = out_date_match ? out_date_match[1] : '2026-03-30';
          pc_link = `https://www.ly.com/hotel/hoteldetail?hotelid=${resource_id}&inDate=${in_date}&outDate=${out_date}`;
        } else {
          pc_link = raw_pc_link || '#';
        }
      } else {
        pc_link = hotel.pcRedirectUrl || hotel.clawRedirectUrl || hotel.redirectUrl || '#';
      }
      
      const mobile_link = hotel.clawRedirectUrl || hotel.redirectUrl || '#';
      
      let pc_link_md, mobile_link_md;
      if (use_plain_link) {
        pc_link_md = pc_link !== '#' ? pc_link : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? mobile_link : '暂不可用';
      } else {
        pc_link_md = pc_link !== '#' ? `[PC 端](${pc_link})` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `[手机端](${mobile_link})` : '暂不可用';
      }
      
      output += `| ${name} | ${price} | ${star} | ⭐${score}（${comment_num}条） | ${address} | ${pc_link_md} | ${mobile_link_md} |\n`;
    });
  } else {
    // 卡片格式
    hotels.forEach((hotel) => {
      const name = hotel.name || '未知酒店';
      const price = hotel.price ? `¥${hotel.price}` : '暂无价格';
      const star = hotel.star || '未评级';
      const score = hotel.score || '暂无';
      const comment_num = hotel.commentNum || '0';
      const describe = hotel.describe || '无';
      const address = hotel.address || '';
      const resource_id = hotel.resourceId || '';
      
      // 构建链接 - PC 详情页使用酒店 ID 构建
      let pc_link = '#';
      if (resource_id) {
        const raw_pc_link = hotel.pcRedirectUrl || '';
        if (raw_pc_link.includes('hoteldetail')) {
          pc_link = raw_pc_link;
        } else if (raw_pc_link.includes('hotellist')) {
          const in_date_match = raw_pc_link.match(/inDate=([^&]+)/);
          const out_date_match = raw_pc_link.match(/outDate=([^&]+)/);
          const in_date = in_date_match ? in_date_match[1] : '2026-03-29';
          const out_date = out_date_match ? out_date_match[1] : '2026-03-30';
          pc_link = `https://www.ly.com/hotel/hoteldetail?hotelid=${resource_id}&inDate=${in_date}&outDate=${out_date}`;
        } else {
          pc_link = raw_pc_link || '#';
        }
      } else {
        pc_link = hotel.pcRedirectUrl || hotel.clawRedirectUrl || hotel.redirectUrl || '#';
      }
      
      const mobile_link = hotel.clawRedirectUrl || hotel.redirectUrl || '#';
      
      let pc_link_md, mobile_link_md;
      if (use_plain_link) {
        pc_link_md = pc_link !== '#' ? `PC 端：${pc_link}` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `手机端：${mobile_link}` : '暂不可用';
      } else {
        pc_link_md = pc_link !== '#' ? `[PC 端](${pc_link})` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `[手机端](${mobile_link})` : '暂不可用';
      }
      
      output += `### 🏨 ${name}\n`;
      output += `**价格** ${price}/晚起 | **类型** ${star} | **评分** ⭐${score}（${comment_num}条）\n`;
      output += `**特点** ${describe}\n`;
      if (address) output += `**地址** ${address}\n`;
      output += `**预订** ${pc_link_md} | ${mobile_link_md}\n`;
      output += '\n---\n\n';
    });
  }
  
  output += '💡 **更多选择**：也可以打开 **同程旅行 APP** 或在 **微信 - 我 - 服务** 中，点击 **火车票机票** 以及 **酒店民宿** 查看更丰富的资源。\n';
  output += '\n';
  return output;
}

/**
 * 格式化景区结果（卡片式列表）
 * @param {object} scenery_data - 景区数据
 * @param {boolean} use_table - 是否使用表格格式
 * @param {boolean} use_plain_link - 是否使用纯文本链接（微信渠道）
 * @returns {string} - 格式化输出
 */
function format_scenery_result(scenery_data, use_table = false, use_plain_link = false) {
  if (!scenery_data || !scenery_data.sceneryList) {
    return '未找到相关景区信息';
  }
  
  const sceneries = scenery_data.sceneryList.slice(0, 5);
  // 获取顶层 PC 链接（列表页）作为备选
  const page_pc_link = scenery_data.pageDataList?.[0]?.pcRedirectUrl || '';
  
  let output = '🏞️ 景区查询结果：\n\n';
  
  if (use_table) {
    // 表格格式
    output += '| 景区名称 | 城市 | 门票 | 评分 | 开放时间 | PC 预订 | 手机预订 |\n';
    output += '|----------|------|------|------|----------|--------|---------|\n';
    
    sceneries.forEach((scenery) => {
      const name = scenery.name || '未知景区';
      const city = scenery.cityName || '-';
      const star = scenery.star || '未评级';
      const score = scenery.score || '暂无';
      const comment_num = scenery.commentNum || '0';
      const price = scenery.price ? `¥${scenery.price}` : '暂无价格';
      const open_time = scenery.openTime || '未公布';
      const describe = scenery.describe || '';
      
      // 构建链接 - 优先使用景区自己的链接
      const pc_link = scenery.pcRedirectUrl || page_pc_link || '#';
      const mobile_link = scenery.clawRedirectUrl || scenery.redirectUrl || '#';
      
      let pc_link_md, mobile_link_md;
      if (use_plain_link) {
        pc_link_md = pc_link !== '#' ? pc_link : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? mobile_link : '暂不可用';
      } else {
        pc_link_md = pc_link !== '#' ? `[PC 端](${pc_link})` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `[手机端](${mobile_link})` : '暂不可用';
      }
      
      output += `| ${name} | ${city} | ${price} | ⭐${score}（${comment_num}条） | ${open_time} | ${pc_link_md} | ${mobile_link_md} |\n`;
    });
  } else {
    // 卡片格式
    sceneries.forEach((scenery) => {
      const name = scenery.name || '未知景区';
      const city = scenery.cityName || '-';
      const star = scenery.star || '未评级';
      const score = scenery.score || '暂无';
      const comment_num = scenery.commentNum || '0';
      const price = scenery.price ? `¥${scenery.price}` : '暂无价格';
      const open_time = scenery.openTime || '未公布';
      const describe = scenery.describe || '';
      
      // 构建链接 - 优先使用景区自己的链接
      const pc_link = scenery.pcRedirectUrl || page_pc_link || '#';
      const mobile_link = scenery.clawRedirectUrl || scenery.redirectUrl || '#';
      
      let pc_link_md, mobile_link_md;
      if (use_plain_link) {
        pc_link_md = pc_link !== '#' ? `PC 端：${pc_link}` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `手机端：${mobile_link}` : '暂不可用';
      } else {
        pc_link_md = pc_link !== '#' ? `[PC 端](${pc_link})` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `[手机端](${mobile_link})` : '暂不可用';
      }
      
      output += `### 🏞️ ${name}\n`;
      output += `**城市** ${city} | **星级** ${star} | **评分** ⭐${score}（${comment_num}条）\n`;
      output += `**门票** ${price} | **开放时间** ${open_time}\n`;
      if (describe) output += `**特点** ${describe}\n`;
      output += `**预订** ${pc_link_md} | ${mobile_link_md}\n`;
      output += '\n---\n\n';
    });
  }
  
  output += '💡 **更多选择**：也可以打开 **同程旅行 APP** 或在 **微信 - 我 - 服务** 中，点击 **火车票机票** 以及 **酒店民宿** 查看更丰富的资源。\n';
  output += '\n';
  return output;
}

/**
 * 格式化跟团游/度假产品结果（表格或卡片）
 * @param {object} trip_data - 跟团游数据
 * @param {boolean} use_table - 是否使用表格格式
 * @param {boolean} use_plain_link - 是否使用纯文本链接
 * @returns {string} - 格式化输出
 */
function format_trip_result(trip_data, use_table = false, use_plain_link = false) {
  if (!trip_data || !trip_data.tripList) {
    return '未找到相关跟团游或度假产品信息';
  }
  
  const trips = trip_data.tripList.slice(0, 5);
  
  let output = '🧳 跟团游/度假产品查询结果：\n\n';
  
  if (use_table) {
    // 表格格式
    output += '| 产品 | 目的地 | 价格 | 评分 | 特点 | 预订链接 |\n';
    output += '|------|--------|------|------|------|----------|\n';
    
    trips.forEach((trip) => {
      const name = trip.name || '未知产品';
      const dest_list = (trip.destList || []).join(', ');
      const price = trip.price ? `¥${trip.price}` : '暂无价格';
      const score = trip.score && trip.score !== '0.0' ? `⭐${trip.score}` : '暂无';
      const label_list = (trip.labelList || []).join(', ');
      
      // 跟团游只有 redirectUrl（手机端），没有 pcRedirectUrl
      const mobile_link = trip.clawRedirectUrl || trip.redirectUrl || '#';
      const pc_link = trip.clawRedirectUrl || trip.redirectUrl || '#';  // 同程跟团游 PC 和移动端是同一链接
      
      let pc_link_md, mobile_link_md;
      if (use_plain_link) {
        pc_link_md = pc_link !== '#' ? `PC 端：${pc_link}` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `手机端：${mobile_link}` : '暂不可用';
      } else {
        pc_link_md = pc_link !== '#' ? `[PC 端](${pc_link})` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `[手机端](${mobile_link})` : '暂不可用';
      }
      
      output += `| ${name} | ${dest_list} | ${price} | ${score} | ${label_list} | ${pc_link_md} \\| ${mobile_link_md} |\n`;
    });
  } else {
    // 卡片格式
    trips.forEach((trip) => {
      const name = trip.name || '未知产品';
      const dest_list = (trip.destList || []).join(', ');
      const price = trip.price ? `¥${trip.price}` : '暂无价格';
      const score = trip.score && trip.score !== '0.0' ? `⭐${trip.score}` : '暂无';
      const comment_num = trip.commentNum || '0';
      const label_list = (trip.labelList || []).join(', ');
      
      // 跟团游只有 redirectUrl（手机端），没有 pcRedirectUrl
      const mobile_link = trip.clawRedirectUrl || trip.redirectUrl || '#';
      const pc_link = trip.clawRedirectUrl || trip.redirectUrl || '#';  // 同程跟团游 PC 和移动端是同一链接
      
      let pc_link_md, mobile_link_md;
      if (use_plain_link) {
        pc_link_md = pc_link !== '#' ? `PC 端：${pc_link}` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `手机端：${mobile_link}` : '暂不可用';
      } else {
        pc_link_md = pc_link !== '#' ? `[PC 端](${pc_link})` : '暂不可用';
        mobile_link_md = mobile_link !== '#' ? `[手机端](${mobile_link})` : '暂不可用';
      }
      
      output += `### 🧳 ${name}\n`;
      output += `**目的地** ${dest_list}\n`;
      output += `**价格** ${price} | **评分** ${score}（${comment_num}条）\n`;
      if (label_list) output += `**特点** ${label_list}\n`;
      output += `**预订** ${pc_link_md} | ${mobile_link_md}\n`;
      output += '\n---\n\n';
    });
  }
  
  output += '💡 **更多选择**：也可以打开 **同程旅行 APP** 或在 **微信 - 我 - 服务** 中，点击 **火车票机票** 以及 **酒店民宿** 查看更丰富的资源。\n';
  output += '\n';
  return output;
}

/**
 * 主函数
 */
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length < 1) {
    console.log('用法：node query.js <查询文本> [意图类型]');
    console.log('示例：');
    console.log('  node query.js "北京到上海的火车票" Train');
    console.log('  node query.js "明天飞广州的机票" Flight');
    console.log('  node query.js "上海外滩附近的酒店" Hotel');
    console.log('\n意图类型：Flight, Train, Hotel, Scenery, Travel');
    process.exit(1);
  }
  
  const query = args[0];
  const planning = args[1] || detect_planning(query);
  const channel = args[2] || '';  // 可选：通信渠道
  const surface = args[3] || '';  // 可选：交互界面
  
  // 检测输出格式
  let use_table = false;
  let use_plain_link = false;
  
  if (channel === 'webchat') {
    use_table = true;  // webchat 使用表格
  } else if (channel.includes('wechat') || channel.includes('weixin') || channel.includes('微信')) {
    use_plain_link = true;  // 微信渠道使用纯文本链接
  } else if (surface === 'mobile') {
    use_table = false;  // mobile 使用卡片
  }
  // 其他情况默认使用卡片格式
  
  console.log(`🔍 查询：${query}`);
  console.log(`🎯 意图：${planning}`);
  console.log(`📡 渠道：${channel || '默认'}`);
  console.log(`📱 界面：${surface || '默认'}`);
  console.log(`📊 格式：${use_table ? '表格' : '卡片'} | 链接：${use_plain_link ? '纯文本' : 'Markdown'}`);
  console.log('---\n');
  
  try {
    const result = await query_chengxin(query, planning, channel, surface);
    
    if (result.code === '0' || result.code === 0) {
      console.log('✅ 查询成功\n');
      
      // 根据意图类型格式化输出（响应结构：result.data.data.xxxData）
      const response_data = result.data?.data || result.data;
      if (planning === 'Train' && response_data?.trainData) {
        console.log(format_train_result(response_data.trainData, use_table, use_plain_link));
      } else if (planning === 'Flight' && response_data?.flightData) {
        console.log(format_flight_result(response_data.flightData, use_table, use_plain_link));
      } else if (planning === 'Hotel' && response_data?.hotelData) {
        console.log(format_hotel_result(response_data.hotelData, use_table, use_plain_link));
      } else if (planning === 'Scenery' && response_data?.sceneryData) {
        console.log(format_scenery_result(response_data.sceneryData, use_table, use_plain_link));
      } else if (planning === 'Travel' && response_data?.tripData) {
        console.log(format_trip_result(response_data.tripData, use_table, use_plain_link));
      } else {
        console.log('📦 原始响应：');
        console.log(JSON.stringify(result, null, 2));
      }
    } else if (result.code === '1') {
      console.log('⚠️ 无结果');
    } else {
      console.log(`❌ 查询失败：${result.message || '未知错误'}`);
    }
  } catch (error) {
    console.error(`❌ 错误：${error.message}`);
    process.exit(1);
  }
}

// 导出函数供其他模块使用
module.exports = {
  query_chengxin,
  detect_planning,
  PLANNING_MAP
};

// 运行主函数
if (require.main === module) {
  main();
}
