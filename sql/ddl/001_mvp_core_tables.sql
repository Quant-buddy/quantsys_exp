-- 第一个月 MVP 核心表 DDL 草案
-- Version: v0.1
-- Date: 2026-07-07
-- Scope: 支持第一个月主链路：数据 -> 因子 -> 标签 -> 排名 -> 组合 -> 风控 -> 计划单

create table if not exists dim_stock (
  symbol varchar(16) primary key,
  exchange varchar(8) not null,
  stock_name text not null,
  list_date date,
  delist_date date,
  is_active boolean not null default true,
  source varchar(32) not null,
  run_id varchar(64),
  update_time timestamp not null default now()
);

create table if not exists dim_trade_calendar (
  trade_date date primary key,
  is_open boolean not null,
  pre_trade_date date,
  next_trade_date date,
  source varchar(32) not null,
  run_id varchar(64),
  update_time timestamp not null default now()
);

create table if not exists fact_daily_bar (
  symbol varchar(16) not null,
  trade_date date not null,
  open numeric(18,6),
  high numeric(18,6),
  low numeric(18,6),
  close numeric(18,6),
  pre_close numeric(18,6),
  volume numeric(24,4),
  amount numeric(24,4),
  adj_factor numeric(18,8),
  source varchar(32) not null,
  run_id varchar(64) not null,
  update_time timestamp not null default now(),
  primary key (symbol, trade_date, source)
);

create table if not exists fact_index_daily_bar (
  index_code varchar(16) not null,
  trade_date date not null,
  open numeric(18,6),
  high numeric(18,6),
  low numeric(18,6),
  close numeric(18,6),
  volume numeric(24,4),
  amount numeric(24,4),
  source varchar(32) not null,
  run_id varchar(64) not null,
  update_time timestamp not null default now(),
  primary key (index_code, trade_date, source)
);

create table if not exists fact_stock_status (
  symbol varchar(16) not null,
  trade_date date not null,
  is_st boolean not null default false,
  is_suspended boolean not null default false,
  is_limit_up boolean not null default false,
  is_limit_down boolean not null default false,
  up_limit_price numeric(18,6),
  down_limit_price numeric(18,6),
  listed_days int,
  source varchar(32) not null,
  run_id varchar(64) not null,
  update_time timestamp not null default now(),
  primary key (symbol, trade_date)
);

create table if not exists fact_industry_member (
  symbol varchar(16) not null,
  trade_date date not null,
  industry_code varchar(32),
  industry_name text,
  industry_source varchar(32) not null,
  version varchar(32) not null,
  run_id varchar(64),
  update_time timestamp not null default now(),
  primary key (symbol, trade_date, industry_source, version)
);

create table if not exists fact_financial_indicator (
  symbol varchar(16) not null,
  report_period date not null,
  publish_date date not null,
  indicator_name varchar(64) not null,
  indicator_value numeric(24,8),
  source varchar(32) not null,
  run_id varchar(64) not null,
  update_time timestamp not null default now(),
  primary key (symbol, report_period, publish_date, indicator_name)
);

create table if not exists quality_report (
  report_id varchar(64) primary key,
  trade_date date,
  check_name varchar(128) not null,
  check_status varchar(16) not null,
  severity varchar(16) not null,
  affected_rows int,
  threshold_text text,
  detail text,
  should_block_plan boolean not null default false,
  run_id varchar(64) not null,
  update_time timestamp not null default now()
);

create table if not exists feature_factor_value (
  symbol varchar(16) not null,
  trade_date date not null,
  factor_name varchar(64) not null,
  factor_value numeric(24,10),
  factor_version varchar(32) not null,
  source_quality varchar(16) not null default 'core',
  run_id varchar(64) not null,
  update_time timestamp not null default now(),
  primary key (symbol, trade_date, factor_name, factor_version)
);

create table if not exists label_forward_return (
  symbol varchar(16) not null,
  trade_date date not null,
  horizon int not null,
  forward_return numeric(24,10),
  run_id varchar(64) not null,
  update_time timestamp not null default now(),
  primary key (symbol, trade_date, horizon)
);

create table if not exists signal_score (
  signal_version varchar(64) not null,
  symbol varchar(16) not null,
  trade_date date not null,
  alpha_score numeric(24,10),
  rank_num int,
  score_reason text,
  do_not_trade_reason text,
  run_id varchar(64) not null,
  update_time timestamp not null default now(),
  primary key (signal_version, symbol, trade_date)
);

create table if not exists portfolio_target (
  portfolio_id varchar(64) not null,
  trade_date date not null,
  symbol varchar(16) not null,
  target_weight numeric(18,10) not null,
  target_amount numeric(24,4),
  reason text,
  run_id varchar(64) not null,
  update_time timestamp not null default now(),
  primary key (portfolio_id, trade_date, symbol)
);

create table if not exists risk_check_report (
  report_id varchar(64) primary key,
  trade_date date not null,
  portfolio_id varchar(64),
  symbol varchar(16),
  risk_check_status varchar(16) not null,
  risk_block_reason text,
  check_detail text,
  run_id varchar(64) not null,
  update_time timestamp not null default now()
);

create table if not exists order_plan (
  plan_id varchar(64) not null,
  trade_date date not null,
  account_id varchar(64) not null,
  symbol varchar(16) not null,
  stock_name text,
  side varchar(8) not null,
  target_qty int not null,
  limit_price numeric(18,6),
  target_weight numeric(18,10),
  estimated_amount numeric(24,4),
  order_reason text,
  risk_check_status varchar(16) not null,
  risk_block_reason text,
  approved_by varchar(64),
  run_id varchar(64) not null,
  update_time timestamp not null default now(),
  primary key (plan_id, symbol, side)
);

create table if not exists execution_report (
  trade_date date not null,
  account_id varchar(64) not null,
  symbol varchar(16) not null,
  side varchar(8) not null,
  filled_qty int not null,
  filled_price numeric(18,6) not null,
  commission numeric(18,6),
  tax numeric(18,6),
  trade_time timestamp,
  broker_order_id varchar(128),
  run_id varchar(64),
  import_time timestamp not null default now(),
  primary key (trade_date, account_id, symbol, side, trade_time)
);

create table if not exists holding_snapshot (
  account_id varchar(64) not null,
  trade_date date not null,
  symbol varchar(16) not null,
  quantity int not null,
  market_value numeric(24,4),
  cost_amount numeric(24,4),
  source varchar(32) not null,
  run_id varchar(64) not null,
  update_time timestamp not null default now(),
  primary key (account_id, trade_date, symbol)
);

