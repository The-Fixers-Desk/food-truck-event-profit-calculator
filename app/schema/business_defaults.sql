CREATE TABLE IF NOT EXISTS business_defaults (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    business_name TEXT NOT NULL DEFAULT '',
    average_order_sale_amount_cents INTEGER NOT NULL
        CHECK (average_order_sale_amount_cents > 0),
    food_cost_method TEXT NOT NULL
        CHECK (
            food_cost_method IN (
                'average_per_order',
                'sales_percentage',
                'typical_event_total'
            )
        ),
    average_food_cost_per_order_cents INTEGER
        CHECK (
            average_food_cost_per_order_cents IS NULL
            OR average_food_cost_per_order_cents >= 0
        ),
    food_cost_percentage_basis_points INTEGER
        CHECK (
            food_cost_percentage_basis_points IS NULL
            OR food_cost_percentage_basis_points BETWEEN 0 AND 10000
        ),
    typical_food_cost_total_cents INTEGER
        CHECK (
            typical_food_cost_total_cents IS NULL
            OR typical_food_cost_total_cents >= 0
        ),
    card_sales_basis_points INTEGER NOT NULL
        CHECK (card_sales_basis_points BETWEEN 0 AND 10000),
    card_processing_basis_points INTEGER NOT NULL
        CHECK (card_processing_basis_points BETWEEN 0 AND 10000),
    default_travel_cost_cents INTEGER
        CHECK (
            default_travel_cost_cents IS NULL
            OR default_travel_cost_cents >= 0
        ),
    default_owner_labor_pay_cents INTEGER
        CHECK (
            default_owner_labor_pay_cents IS NULL
            OR default_owner_labor_pay_cents >= 0
        ),
    profit_target_type TEXT
        CHECK (
            profit_target_type IS NULL
            OR profit_target_type IN ('profit_amount', 'profit_margin')
        ),
    minimum_profit_amount_cents INTEGER
        CHECK (
            minimum_profit_amount_cents IS NULL
            OR minimum_profit_amount_cents >= 0
        ),
    minimum_profit_margin_basis_points INTEGER
        CHECK (
            minimum_profit_margin_basis_points IS NULL
            OR minimum_profit_margin_basis_points BETWEEN 0 AND 10000
        ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (
            food_cost_method = 'average_per_order'
            AND average_food_cost_per_order_cents IS NOT NULL
            AND food_cost_percentage_basis_points IS NULL
            AND typical_food_cost_total_cents IS NULL
        )
        OR (
            food_cost_method = 'sales_percentage'
            AND average_food_cost_per_order_cents IS NULL
            AND food_cost_percentage_basis_points IS NOT NULL
            AND typical_food_cost_total_cents IS NULL
        )
        OR (
            food_cost_method = 'typical_event_total'
            AND average_food_cost_per_order_cents IS NULL
            AND food_cost_percentage_basis_points IS NULL
            AND typical_food_cost_total_cents IS NOT NULL
        )
    ),
    CHECK (
        (
            profit_target_type IS NULL
            AND minimum_profit_amount_cents IS NULL
            AND minimum_profit_margin_basis_points IS NULL
        )
        OR (
            profit_target_type = 'profit_amount'
            AND minimum_profit_amount_cents IS NOT NULL
            AND minimum_profit_margin_basis_points IS NULL
        )
        OR (
            profit_target_type = 'profit_margin'
            AND minimum_profit_amount_cents IS NULL
            AND minimum_profit_margin_basis_points IS NOT NULL
        )
    )
);

CREATE TABLE IF NOT EXISTS business_default_labor_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_defaults_id INTEGER NOT NULL DEFAULT 1
        REFERENCES business_defaults(id) ON DELETE CASCADE
        CHECK (business_defaults_id = 1),
    position INTEGER NOT NULL CHECK (position >= 0),
    hourly_rate_cents INTEGER NOT NULL CHECK (hourly_rate_cents >= 0),
    total_paid_minutes INTEGER NOT NULL CHECK (total_paid_minutes >= 0),
    UNIQUE (business_defaults_id, position)
);
