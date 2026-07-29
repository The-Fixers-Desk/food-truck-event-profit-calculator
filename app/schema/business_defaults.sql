CREATE TABLE IF NOT EXISTS business_defaults (
    id INTEGER PRIMARY KEY
        CHECK (id = 1),

    business_name TEXT NOT NULL DEFAULT '',

    average_order_value_cents INTEGER NOT NULL
        CHECK (average_order_value_cents > 0),

    food_cost_basis_points INTEGER NOT NULL
        CHECK (
            food_cost_basis_points >= 0
            AND food_cost_basis_points <= 10000
        ),

    card_sales_basis_points INTEGER NOT NULL
        CHECK (
            card_sales_basis_points >= 0
            AND card_sales_basis_points <= 10000
        ),

    card_processing_basis_points INTEGER NOT NULL
        CHECK (
            card_processing_basis_points >= 0
            AND card_processing_basis_points <= 10000
        ),

    default_staff_count INTEGER NOT NULL
        CHECK (default_staff_count >= 0),

    hourly_labor_cost_cents INTEGER NOT NULL
        CHECK (hourly_labor_cost_cents >= 0),

    setup_minutes INTEGER NOT NULL
        CHECK (setup_minutes >= 0),

    cleanup_minutes INTEGER NOT NULL
        CHECK (cleanup_minutes >= 0),

    vehicle_cost_per_mile_cents INTEGER NOT NULL
        CHECK (vehicle_cost_per_mile_cents >= 0),

    minimum_acceptable_profit_cents INTEGER
        CHECK (
            minimum_acceptable_profit_cents IS NULL
            OR minimum_acceptable_profit_cents >= 0
        ),

    minimum_acceptable_margin_basis_points INTEGER
        CHECK (
            minimum_acceptable_margin_basis_points IS NULL
            OR (
                minimum_acceptable_margin_basis_points >= 0
                AND minimum_acceptable_margin_basis_points <= 10000
            )
        ),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);