export interface SystemHealthResponse {
    overall_status: string;
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    uptime_seconds: number;
    process_memory_mb: number;
    directories_status: Record<string, any>;
    services_status: Record<string, string>;
    health_issues: string[];
    last_check: string;
  }
  
  export interface SystemStatsResponse {
    system_info: Record<string, any>;
    network_stats: Record<string, number>;
    data_stats: Record<string, any>;
    recent_activity: Record<string, any>;
    generated_at: string;
  }
  
  export interface ConfigurationRequest {
    configuration: Record<string, any>;
  }
  
  export interface UserRequest {
    username: string;
    email: string;
    role: string;
  }
  
  export interface UserResponse {
    username: string;
    email: string;
    role: string;
    active: boolean;
    created_at: string;
    last_login?: string;
  }
  
  export interface MaintenanceRequest {
    task_type: string;
    parameters?: Record<string, any>;
  }