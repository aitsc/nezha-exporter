# 介绍
nezha 面板 api 转 prometheus metrics 接口

## 安装
- pip install nezha-exporter
- nezha-prometheus-exporter --endpoint http://dashboard.example.com:8008 --endpoint-token xxx
- 配置 prometheus.yml
```yaml
scrape_configs:
  - job_name: 'nezha'
    static_configs:
      - targets: ['localhost:9221']
```
