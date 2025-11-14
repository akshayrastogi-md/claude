"""
Facebook Ads integration module for marketing analytics
"""
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class FacebookAdsIntegration:
    """
    Facebook Marketing API integration

    Features:
    - Campaign performance metrics
    - Ad spend tracking
    - ROAS (Return on Ad Spend) calculation
    - Audience insights
    - Instagram ads included
    """

    def __init__(self, access_token: str, ad_account_id: str):
        """
        Initialize Facebook Ads integration

        Args:
            access_token: Facebook access token
            ad_account_id: Ad account ID (format: act_123456789)
        """
        self.access_token = access_token
        self.ad_account_id = ad_account_id if ad_account_id.startswith('act_') else f'act_{ad_account_id}'
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to Facebook API"""
        if params is None:
            params = {}

        params['access_token'] = self.access_token

        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def get_campaigns(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch campaigns with performance metrics

        Args:
            date_from: Start date for metrics
            date_to: End date for metrics
            status: Campaign statuses to filter (ACTIVE, PAUSED, DELETED, ARCHIVED)

        Returns:
            List of campaigns with metrics
        """
        if status is None:
            status = ["ACTIVE", "PAUSED"]

        # Date range for insights
        if not date_to:
            date_to = datetime.now()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        params = {
            "fields": "id,name,status,objective,daily_budget,lifetime_budget,start_time,stop_time,insights{spend,impressions,clicks,conversions,ctr,cpc,cpm,actions,action_values}",
            "filtering": f'[{{"field":"status","operator":"IN","value":{status}}}]',
            "time_range": {
                "since": date_from.strftime("%Y-%m-%d"),
                "until": date_to.strftime("%Y-%m-%d")
            }
        }

        response = self._make_request(f"{self.ad_account_id}/campaigns", params)
        return response.get("data", [])

    def get_campaign_insights(
        self,
        campaign_id: str,
        date_from: datetime,
        date_to: datetime
    ) -> Dict[str, Any]:
        """
        Get detailed insights for a specific campaign

        Args:
            campaign_id: Campaign ID
            date_from: Start date
            date_to: End date

        Returns:
            Campaign insights
        """
        params = {
            "fields": "spend,impressions,clicks,ctr,cpc,cpm,conversions,actions,action_values,cost_per_conversion",
            "time_range": {
                "since": date_from.strftime("%Y-%m-%d"),
                "until": date_to.strftime("%Y-%m-%d")
            },
            "level": "campaign"
        }

        response = self._make_request(f"{campaign_id}/insights", params)
        data = response.get("data", [])
        return data[0] if data else {}

    def sync_campaigns_to_db(
        self,
        db,
        store_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ):
        """
        Sync Facebook campaigns to database

        Args:
            db: Database session
            store_id: Store ID
            date_from: Start date
            date_to: End date
        """
        from app.models import MarketingCampaign

        fb_campaigns = self.get_campaigns(date_from, date_to)

        for fb_campaign in fb_campaigns:
            insights = fb_campaign.get("insights", {}).get("data", [{}])[0]

            # Check if campaign exists
            existing = db.query(MarketingCampaign).filter(
                MarketingCampaign.store_id == store_id,
                MarketingCampaign.platform_campaign_id == fb_campaign["id"]
            ).first()

            # Extract metrics
            spend = float(insights.get("spend", 0))
            impressions = int(insights.get("impressions", 0))
            clicks = int(insights.get("clicks", 0))
            ctr = float(insights.get("ctr", 0))
            cpc = float(insights.get("cpc", 0))

            # Extract conversions
            conversions = 0
            revenue = 0.0

            for action in insights.get("actions", []):
                if action.get("action_type") == "purchase":
                    conversions = int(action.get("value", 0))

            for action_value in insights.get("action_values", []):
                if action_value.get("action_type") == "purchase":
                    revenue = float(action_value.get("value", 0))

            # Calculate ROAS
            roas = (revenue / spend) if spend > 0 else 0.0
            cpa = (spend / conversions) if conversions > 0 else 0.0

            if existing:
                # Update existing campaign
                existing.spent = spend
                existing.impressions = impressions
                existing.clicks = clicks
                existing.conversions = conversions
                existing.revenue = revenue
                existing.ctr = ctr
                existing.cpc = cpc
                existing.cpa = cpa
                existing.roas = roas
                existing.last_synced_at = datetime.utcnow()
            else:
                # Create new campaign
                campaign = MarketingCampaign(
                    store_id=store_id,
                    name=fb_campaign.get("name"),
                    channel="facebook",
                    campaign_type=fb_campaign.get("objective", "").lower(),
                    platform_campaign_id=fb_campaign["id"],
                    budget=float(fb_campaign.get("daily_budget", 0)) if fb_campaign.get("daily_budget") else float(fb_campaign.get("lifetime_budget", 0)),
                    spent=spend,
                    impressions=impressions,
                    clicks=clicks,
                    conversions=conversions,
                    revenue=revenue,
                    ctr=ctr,
                    cpc=cpc,
                    cpa=cpa,
                    roas=roas,
                    status=fb_campaign.get("status", "").lower(),
                    start_date=datetime.fromisoformat(fb_campaign["start_time"].replace("Z", "+00:00")) if fb_campaign.get("start_time") else None,
                    end_date=datetime.fromisoformat(fb_campaign["stop_time"].replace("Z", "+00:00")) if fb_campaign.get("stop_time") else None,
                    last_synced_at=datetime.utcnow()
                )
                db.add(campaign)

        db.commit()
        return len(fb_campaigns)

    def get_ad_account_info(self) -> Dict[str, Any]:
        """Get ad account information"""
        params = {
            "fields": "id,name,account_status,currency,timezone_name,business"
        }

        return self._make_request(self.ad_account_id, params)

    @staticmethod
    def generate_auth_url(client_id: str, redirect_uri: str, scopes: List[str]) -> str:
        """
        Generate Facebook OAuth URL

        Args:
            client_id: Facebook App ID
            redirect_uri: Redirect URI
            scopes: Permission scopes

        Returns:
            Authorization URL
        """
        scope_string = ",".join(scopes)
        return (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope_string}&"
            f"response_type=code"
        )

    def exchange_code_for_token(self, code: str, client_id: str, client_secret: str, redirect_uri: str) -> str:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code
            client_id: Facebook App ID
            client_secret: Facebook App Secret
            redirect_uri: Redirect URI

        Returns:
            Access token
        """
        url = f"{self.base_url}/oauth/access_token"
        params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json().get("access_token")
