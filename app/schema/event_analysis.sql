CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL CHECK (length(trim(event_name)) > 0),
    event_date TEXT NOT NULL CHECK (length(trim(event_date)) > 0),
    start_time_minutes INTEGER NOT NULL
        CHECK (start_time_minutes BETWEEN 0 AND 1439),
    location TEXT NOT NULL CHECK (length(trim(location)) > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL
        REFERENCES events(id) ON DELETE CASCADE,
    scenario_name TEXT NOT NULL CHECK (length(trim(scenario_name)) > 0),
    notes TEXT,

    estimated_attendance INTEGER NOT NULL
        CHECK (estimated_attendance >= 0),
    other_competing_food_vendors INTEGER NOT NULL
        CHECK (other_competing_food_vendors >= 0),
    expected_food_buyer_basis_points INTEGER NOT NULL
        CHECK (expected_food_buyer_basis_points BETWEEN 0 AND 10000),

    event_protection TEXT NOT NULL
        CHECK (
            event_protection IN (
                'fully_indoors',
                'covered_reliable_seating',
                'partially_covered',
                'fully_outdoors'
            )
        ),
    weather_outlook TEXT NOT NULL
        CHECK (
            weather_outlook IN (
                'favorable',
                'minor_concern',
                'moderate_adverse',
                'significant_adverse',
                'severe_disruption',
                'custom'
            )
        ),
    custom_weather_reduction_basis_points INTEGER
        CHECK (
            custom_weather_reduction_basis_points IS NULL
            OR custom_weather_reduction_basis_points BETWEEN 0 AND 10000
        ),

    revenue_method TEXT NOT NULL
        CHECK (revenue_method IN ('attendance', 'manual_sales')),
    average_order_sale_amount_cents INTEGER
        CHECK (
            average_order_sale_amount_cents IS NULL
            OR average_order_sale_amount_cents >= 0
        ),
    expected_sales_amount_cents INTEGER
        CHECK (
            expected_sales_amount_cents IS NULL
            OR expected_sales_amount_cents >= 0
        ),
    manual_average_order_sale_amount_cents INTEGER
        CHECK (
            manual_average_order_sale_amount_cents IS NULL
            OR manual_average_order_sale_amount_cents >= 0
        ),

    food_cost_method TEXT NOT NULL
        CHECK (
            food_cost_method IN (
                'average_per_order',
                'sales_percentage',
                'manual_event_total'
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
    manual_food_cost_total_cents INTEGER
        CHECK (
            manual_food_cost_total_cents IS NULL
            OR manual_food_cost_total_cents >= 0
        ),

    card_sales_basis_points INTEGER NOT NULL
        CHECK (card_sales_basis_points BETWEEN 0 AND 10000),
    card_processing_basis_points INTEGER NOT NULL
        CHECK (card_processing_basis_points BETWEEN 0 AND 10000),
    fixed_card_processing_fee_cents INTEGER
        CHECK (
            fixed_card_processing_fee_cents IS NULL
            OR fixed_card_processing_fee_cents >= 0
        ),
    vendor_or_booking_fee_cents INTEGER NOT NULL
        CHECK (vendor_or_booking_fee_cents >= 0),
    organizer_commission_basis_points INTEGER
        CHECK (
            organizer_commission_basis_points IS NULL
            OR organizer_commission_basis_points BETWEEN 0 AND 10000
        ),

    owner_labor_pay_cents INTEGER
        CHECK (
            owner_labor_pay_cents IS NULL
            OR owner_labor_pay_cents >= 0
        ),
    travel_cost_cents INTEGER
        CHECK (travel_cost_cents IS NULL OR travel_cost_cents >= 0),

    profit_target_type TEXT NOT NULL
        CHECK (
            profit_target_type IN ('profit_amount', 'profit_margin')
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
            weather_outlook = 'custom'
            AND custom_weather_reduction_basis_points IS NOT NULL
        )
        OR (
            weather_outlook <> 'custom'
            AND custom_weather_reduction_basis_points IS NULL
        )
    ),
    CHECK (
        (
            revenue_method = 'attendance'
            AND manual_average_order_sale_amount_cents IS NULL
        )
        OR (
            revenue_method = 'manual_sales'
            AND manual_average_order_sale_amount_cents IS NOT NULL
        )
    ),
    CHECK (
        (
            revenue_method = 'attendance'
            AND average_order_sale_amount_cents IS NOT NULL
            AND expected_sales_amount_cents IS NULL
        )
        OR (
            revenue_method = 'manual_sales'
            AND average_order_sale_amount_cents IS NULL
            AND expected_sales_amount_cents IS NOT NULL
        )
    ),
    CHECK (
        (
            food_cost_method = 'average_per_order'
            AND average_food_cost_per_order_cents IS NOT NULL
            AND food_cost_percentage_basis_points IS NULL
            AND manual_food_cost_total_cents IS NULL
        )
        OR (
            food_cost_method = 'sales_percentage'
            AND average_food_cost_per_order_cents IS NULL
            AND food_cost_percentage_basis_points IS NOT NULL
            AND manual_food_cost_total_cents IS NULL
        )
        OR (
            food_cost_method = 'manual_event_total'
            AND average_food_cost_per_order_cents IS NULL
            AND food_cost_percentage_basis_points IS NULL
            AND manual_food_cost_total_cents IS NOT NULL
        )
    ),
    CHECK (
        (
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

CREATE INDEX IF NOT EXISTS event_scenarios_event_id_index
    ON event_scenarios(event_id);

CREATE UNIQUE INDEX IF NOT EXISTS event_scenario_name_unique
    ON event_scenarios(event_id, lower(trim(scenario_name)));

CREATE TABLE IF NOT EXISTS event_scenario_employee_labor_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_scenario_id INTEGER NOT NULL
        REFERENCES event_scenarios(id) ON DELETE CASCADE,
    position INTEGER NOT NULL CHECK (position >= 0),
    hourly_rate_cents INTEGER NOT NULL CHECK (hourly_rate_cents >= 0),
    total_paid_minutes INTEGER NOT NULL CHECK (total_paid_minutes >= 0),
    UNIQUE (event_scenario_id, position)
);

CREATE TABLE IF NOT EXISTS event_scenario_additional_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_scenario_id INTEGER NOT NULL
        REFERENCES event_scenarios(id) ON DELETE CASCADE,
    position INTEGER NOT NULL CHECK (position >= 0),
    cost_name TEXT NOT NULL CHECK (length(trim(cost_name)) > 0),
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    UNIQUE (event_scenario_id, position)
);
