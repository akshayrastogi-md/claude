// MongoDB initialization script
// Creates database, collections, and indexes

db = db.getSiblingDB('d2c_analytics');

// Create collections
db.createCollection('analytics_events');
db.createCollection('user_sessions');
db.createCollection('api_logs');
db.createCollection('metrics_timeseries');
db.createCollection('campaign_performance');
db.createCollection('audit_logs');
db.createCollection('integration_logs');
db.createCollection('forecast_cache');
db.createCollection('analytics_cache');

// Create indexes for analytics_events
db.analytics_events.createIndex({ store_id: 1, timestamp: -1 });
db.analytics_events.createIndex({ event_type: 1 });
db.analytics_events.createIndex({ timestamp: -1 });

// Create indexes for API logs
db.api_logs.createIndex({ timestamp: -1 });
db.api_logs.createIndex({ store_id: 1, timestamp: -1 });
db.api_logs.createIndex({ endpoint: 1 });
db.api_logs.createIndex({ status_code: 1 });

// Create indexes for user sessions
db.user_sessions.createIndex({ user_id: 1, created_at: -1 });
db.user_sessions.createIndex({ session_id: 1 }, { unique: true });
db.user_sessions.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });

// Create indexes for audit logs
db.audit_logs.createIndex({ store_id: 1, timestamp: -1 });
db.audit_logs.createIndex({ user_id: 1, timestamp: -1 });
db.audit_logs.createIndex({ action: 1 });

// Create TTL indexes for cache collections (expire after 1 hour)
db.forecast_cache.createIndex({ created_at: 1 }, { expireAfterSeconds: 3600 });
db.analytics_cache.createIndex({ created_at: 1 }, { expireAfterSeconds: 3600 });

// Create indexes for integration logs
db.integration_logs.createIndex({ store_id: 1, timestamp: -1 });
db.integration_logs.createIndex({ platform: 1, timestamp: -1 });
db.integration_logs.createIndex({ status: 1 });

// Create time-series collection for metrics
db.createCollection('metrics_timeseries', {
    timeseries: {
        timeField: 'timestamp',
        metaField: 'metadata',
        granularity: 'hours'
    }
});

// Create capped collection for real-time logs (100MB limit)
db.createCollection('realtime_logs', {
    capped: true,
    size: 104857600,  // 100MB
    max: 100000
});

print('MongoDB initialized successfully!');
