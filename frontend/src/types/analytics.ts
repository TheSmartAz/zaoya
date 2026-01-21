// Analytics types
export interface DailyAnalytics {
  date: string;
  views: number;
  visitors: number;
  clicks: number;
  submissions: number;
}

export interface AnalyticsTotals {
  views: number;
  unique_visitors: number;
  cta_clicks: number;
  form_submissions: number;
}

export interface AnalyticsTrends {
  views: number; // Percentage change
  visitors: number; // Percentage change
}

export interface AnalyticsResponse {
  period: {
    start: string;
    end: string;
    days: number;
  };
  totals: AnalyticsTotals;
  trends: AnalyticsTrends;
  daily: DailyAnalytics[];
}
