/**
 * OpenClaw安全卫士 - RBAC多角色多级权限隔离模块
 * Author: Mr付Y
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 默认权限定义
const DEFAULT_PERMISSIONS = {
  admin: [
    '*', // 所有权限
  ],
  user: [
    'read',
    'chat',
    'search',
    'generate',
  ],
  guest: [
    'read',
    'chat',
  ]
};

class RBACManager {
  constructor(configPath = './rbac-config.json') {
    this.configPath = configPath;
    this.roles = new Map();
    this.currentUser = null;
    this.loadConfig();
  }

  // 密码哈希
  hashPassword(password) {
    return crypto.createHash('sha256').update(password).digest('hex');
  }

  // 加载配置
  loadConfig() {
    try {
      if (fs.existsSync(this.configPath)) {
        const data = JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
        this.roles = new Map(Object.entries(data.roles));
      } else {
        // 创建默认配置
        this.addRole('admin', 'admin', this.hashPassword('admin'), DEFAULT_PERMISSIONS.admin, 'Administrator');
        this.saveConfig();
      }
    } catch (error) {
      console.error('Failed to load RBAC config:', error);
      this.roles = new Map();
    }
  }

  // 保存配置
  saveConfig() {
    try {
      const data = {
        roles: Object.fromEntries(this.roles)
      };
      const dir = path.dirname(this.configPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(this.configPath, JSON.stringify(data, null, 2));
      return true;
    } catch (error) {
      console.error('Failed to save RBAC config:', error);
      return false;
    }
  }

  // 添加角色
  addRole(roleId, roleName, passwordHash, permissions, description = '') {
    this.roles.set(roleId, {
      roleId,
      roleName,
      passwordHash,
      permissions,
      description,
      createTime: new Date().toISOString()
    });
    this.saveConfig();
    return true;
  }

  // 删除角色
  deleteRole(roleId) {
    const result = this.roles.delete(roleId);
    this.saveConfig();
    return result;
  }

  // 用户登录验证
  authenticate(roleId, password) {
    const role = this.roles.get(roleId);
    if (!role) {
      return { success: false, message: '角色不存在' };
    }
    
    const passwordHash = this.hashPassword(password);
    if (role.passwordHash !== passwordHash) {
      return { success: false, message: '密码错误' };
    }
    
    this.currentUser = role;
    return { 
      success: true, 
      message: '登录成功',
      role: {
        roleId: role.roleId,
        roleName: role.roleName,
        description: role.description
      }
    };
  }

  // 退出登录
  logout() {
    this.currentUser = null;
    return true;
  }

  // 检查当前用户是否有指定权限
  hasPermission(permission) {
    if (!this.currentUser) {
      return false;
    }
    
    // 管理员拥有所有权限
    if (this.currentUser.permissions.includes('*')) {
      return true;
    }
    
    return this.currentUser.permissions.includes(permission);
  }

  // 获取当前登录用户信息
  getCurrentUser() {
    if (!this.currentUser) {
      return null;
    }
    return {
      roleId: this.currentUser.roleId,
      roleName: this.currentUser.roleName,
      description: this.currentUser.description
    };
  }

  // 获取所有角色列表
  getAllRoles() {
    return Array.from(this.roles.values()).map(role => ({
      roleId: role.roleId,
      roleName: role.roleName,
      description: role.description,
      permissions: role.permissions,
      createTime: role.createTime
    }));
  }

  // 更新角色权限
  updatePermissions(roleId, permissions) {
    const role = this.roles.get(roleId);
    if (!role) {
      return false;
    }
    role.permissions = permissions;
    this.roles.set(roleId, role);
    this.saveConfig();
    return true;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = RBACManager;
}
