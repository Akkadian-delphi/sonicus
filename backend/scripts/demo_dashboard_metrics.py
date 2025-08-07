"""
Super Admin Dashboard Metrics API - Usage Examples

This script demonstrates how to use the dashboard metrics API endpoints
in a real application scenario.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any


class DashboardMetricsDemo:
    """
    Demo class showing how to integrate with the Dashboard Metrics API
    """
    
    def __init__(self, base_url: str = "http://localhost:8100"):
        self.base_url = base_url
        self.api_prefix = "/api/v1/super-admin/dashboard"
    
    async def demo_platform_stats(self):
        """Demonstrate platform statistics endpoint usage"""
        print("📊 PLATFORM STATISTICS DEMO")
        print("=" * 50)
        
        # Example API call parameters
        time_ranges = ["1d", "7d", "30d", "90d"]
        
        for time_range in time_ranges:
            print(f"\n📈 Platform stats for {time_range}:")
            
            # In a real app, you'd make HTTP requests like:
            # response = await httpx.get(f"{self.base_url}{self.api_prefix}/stats?time_range={time_range}")
            # data = response.json()
            
            # Mock response structure
            mock_data = {
                "overview": {
                    "total_users": 2500 + (100 if time_range == "90d" else 50),
                    "total_organizations": 125 + (10 if time_range == "90d" else 5),
                    "active_subscriptions": 380 + (20 if time_range == "90d" else 10),
                    "total_sounds": 850,
                    "total_revenue": 11397.00 + (500 if time_range == "90d" else 250),
                    "revenue_growth_percent": 15.2 if time_range == "90d" else 8.5
                },
                "growth": {
                    "time_range": time_range,
                    "new_users": {"1d": 12, "7d": 75, "30d": 320, "90d": 890}[time_range],
                    "new_organizations": {"1d": 1, "7d": 5, "30d": 18, "90d": 45}[time_range],
                },
                "engagement": {
                    "daily_active_users": 750,
                    "monthly_active_users": 1800,
                    "avg_session_duration": 1240,
                    "total_content_plays": 112500
                }
            }
            
            print(f"  • Users: {mock_data['overview']['total_users']:,}")
            print(f"  • Organizations: {mock_data['overview']['total_organizations']:,}")
            print(f"  • Revenue: ${mock_data['overview']['total_revenue']:,.2f}")
            print(f"  • New Users: {mock_data['growth']['new_users']:,}")
            print(f"  • Revenue Growth: {mock_data['overview']['revenue_growth_percent']}%")
    
    async def demo_revenue_analytics(self):
        """Demonstrate revenue analytics endpoint usage"""
        print("\n\n💰 REVENUE ANALYTICS DEMO")
        print("=" * 50)
        
        breakdown_types = ["daily", "weekly", "monthly"]
        
        for breakdown in breakdown_types:
            print(f"\n📊 Revenue analytics - {breakdown} breakdown:")
            
            # Mock revenue data
            mock_data = {
                "summary": {
                    "total_revenue": 45500.00,
                    "avg_revenue_per_period": {
                        "daily": 1516.67,
                        "weekly": 6500.00,
                        "monthly": 22750.00
                    }[breakdown],
                    "growth_rate_percent": 12.5,
                    "active_subscriptions": 380
                },
                "metrics": {
                    "monthly_recurring_revenue": 11397.00,
                    "average_revenue_per_user": 29.99,
                    "churn_rate_percent": 2.5,
                    "customer_lifetime_value": 1439.52
                }
            }
            
            print(f"  • Total Revenue: ${mock_data['summary']['total_revenue']:,.2f}")
            print(f"  • Avg Revenue per {breakdown[:-2]}y: ${mock_data['summary']['avg_revenue_per_period']:,.2f}")
            print(f"  • MRR: ${mock_data['metrics']['monthly_recurring_revenue']:,.2f}")
            print(f"  • ARPU: ${mock_data['metrics']['average_revenue_per_user']:.2f}")
            print(f"  • Churn Rate: {mock_data['metrics']['churn_rate_percent']}%")
            print(f"  • CLV: ${mock_data['metrics']['customer_lifetime_value']:,.2f}")
    
    async def demo_growth_trends(self):
        """Demonstrate growth trends endpoint usage"""
        print("\n\n📈 GROWTH TRENDS DEMO")
        print("=" * 50)
        
        # Mock growth data
        mock_data = {
            "summary": {
                "current_users": 2500,
                "current_organizations": 125,
                "user_growth_rate_percent": 18.5,
                "organization_growth_rate_percent": 22.0
            },
            "acquisition_channels": [
                {"channel": "Organic Search", "users": 1000, "cost_per_acquisition": 0},
                {"channel": "Social Media", "users": 625, "cost_per_acquisition": 15.50},
                {"channel": "Referrals", "users": 500, "cost_per_acquisition": 8.75},
                {"channel": "Paid Ads", "users": 250, "cost_per_acquisition": 32.00},
                {"channel": "Direct", "users": 125, "cost_per_acquisition": 0}
            ],
            "retention_metrics": {
                "day_1_retention": 85.2,
                "day_7_retention": 72.8,
                "day_30_retention": 58.5,
                "day_90_retention": 45.2
            },
            "forecast_30_days": {
                "forecasted_users": 2750,
                "forecasted_organizations": 140,
                "confidence_level": 75
            }
        }
        
        print(f"📊 Current Growth Status:")
        print(f"  • Users: {mock_data['summary']['current_users']:,} ({mock_data['summary']['user_growth_rate_percent']}% growth)")
        print(f"  • Organizations: {mock_data['summary']['current_organizations']:,} ({mock_data['summary']['organization_growth_rate_percent']}% growth)")
        
        print(f"\n🎯 Top Acquisition Channels:")
        for channel in mock_data['acquisition_channels'][:3]:
            cpa_text = f"${channel['cost_per_acquisition']:.2f}" if channel['cost_per_acquisition'] > 0 else "Free"
            print(f"  • {channel['channel']}: {channel['users']:,} users (CPA: {cpa_text})")
        
        print(f"\n🔄 Retention Rates:")
        retention = mock_data['retention_metrics']
        print(f"  • Day 1: {retention['day_1_retention']}%")
        print(f"  • Day 7: {retention['day_7_retention']}%")
        print(f"  • Day 30: {retention['day_30_retention']}%")
        print(f"  • Day 90: {retention['day_90_retention']}%")
        
        print(f"\n🔮 30-Day Forecast:")
        forecast = mock_data['forecast_30_days']
        print(f"  • Forecasted Users: {forecast['forecasted_users']:,}")
        print(f"  • Forecasted Organizations: {forecast['forecasted_organizations']:,}")
        print(f"  • Confidence Level: {forecast['confidence_level']}%")
    
    async def demo_system_health(self):
        """Demonstrate system health endpoint usage"""
        print("\n\n🏥 SYSTEM HEALTH DEMO")
        print("=" * 50)
        
        # Mock health data
        mock_data = {
            "overall_status": "healthy",
            "overall_score": 92.5,
            "component_health": [
                {"component": "Database", "status": "healthy", "score": 95, "details": "Connection pools: 3"},
                {"component": "Cache", "status": "healthy", "score": 88, "details": "Hit rate: 87.3%"},
                {"component": "Background Jobs", "status": "healthy", "score": 90, "details": "Queues available: 4"},
                {"component": "Performance", "status": "warning", "score": 85, "details": "Avg response: 0.85s"},
                {"component": "System Resources", "status": "healthy", "score": 98, "details": "CPU: 25%, Memory: 68%"}
            ],
            "system_metrics": {
                "uptime_hours": 168,
                "total_requests_24h": 45670,
                "error_rate_24h": 12,
                "avg_response_time": 0.85
            }
        }
        
        print(f"🎯 Overall System Health: {mock_data['overall_status'].upper()} ({mock_data['overall_score']}/100)")
        
        print(f"\n🔧 Component Health:")
        for component in mock_data['component_health']:
            status_emoji = {"healthy": "✅", "warning": "⚠️", "critical": "❌"}[component['status']]
            print(f"  {status_emoji} {component['component']}: {component['score']}/100 - {component['details']}")
        
        print(f"\n📊 System Metrics:")
        metrics = mock_data['system_metrics']
        print(f"  • Uptime: {metrics['uptime_hours']} hours")
        print(f"  • Requests (24h): {metrics['total_requests_24h']:,}")
        print(f"  • Error Rate (24h): {metrics['error_rate_24h']}")
        print(f"  • Avg Response Time: {metrics['avg_response_time']:.2f}s")
    
    async def demo_system_alerts(self):
        """Demonstrate system alerts endpoint usage"""
        print("\n\n🚨 SYSTEM ALERTS DEMO")
        print("=" * 50)
        
        # Mock alerts data
        mock_data = {
            "alerts": [
                {
                    "id": "alert_001",
                    "type": "performance",
                    "severity": "warning",
                    "title": "High Response Times Detected",
                    "message": "Average response time: 1.25s",
                    "count": 1,
                    "affected_users": 0,
                    "last_seen": "2025-07-26T21:30:00Z",
                    "component": "api"
                },
                {
                    "id": "error_12345",
                    "type": "error",
                    "severity": "critical",
                    "title": "Recurring Error: DATABASE",
                    "message": "Connection timeout in user authentication",
                    "count": 15,
                    "affected_users": 8,
                    "last_seen": "2025-07-26T21:25:00Z",
                    "component": "authentication"
                }
            ],
            "summary": {
                "total_alerts": 2,
                "critical_count": 1,
                "warning_count": 1,
                "info_count": 0,
                "last_24h_errors": 27
            }
        }
        
        print(f"📊 Alert Summary:")
        summary = mock_data['summary']
        print(f"  • Total Alerts: {summary['total_alerts']}")
        print(f"  • Critical: {summary['critical_count']}")
        print(f"  • Warning: {summary['warning_count']}")
        print(f"  • Errors (24h): {summary['last_24h_errors']}")
        
        print(f"\n🚨 Recent Alerts:")
        for alert in mock_data['alerts']:
            severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[alert['severity']]
            print(f"  {severity_emoji} {alert['title']}")
            print(f"    • Component: {alert['component']}")
            print(f"    • Message: {alert['message']}")
            print(f"    • Count: {alert['count']}")
            if alert['affected_users'] > 0:
                print(f"    • Affected Users: {alert['affected_users']}")
            print(f"    • Last Seen: {alert['last_seen']}")
            print()


async def main():
    """Run the complete dashboard metrics demo"""
    print("🎉 SUPER ADMIN DASHBOARD METRICS API DEMO")
    print("🚀 Sonicus B2B2C Platform Analytics")
    print("=" * 60)
    
    demo = DashboardMetricsDemo()
    
    # Run all demos
    await demo.demo_platform_stats()
    await demo.demo_revenue_analytics()
    await demo.demo_growth_trends()
    await demo.demo_system_health()
    await demo.demo_system_alerts()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETED SUCCESSFULLY!")
    print("\n🔗 API Endpoints Available:")
    print("• GET /api/v1/super-admin/dashboard/stats")
    print("• GET /api/v1/super-admin/dashboard/revenue")
    print("• GET /api/v1/super-admin/dashboard/growth")
    print("• GET /api/v1/super-admin/dashboard/health")
    print("• GET /api/v1/super-admin/dashboard/alerts")
    print("\n📚 Full documentation available at: /docs")
    print("🔐 Super Admin authentication required for all endpoints")


if __name__ == "__main__":
    asyncio.run(main())
