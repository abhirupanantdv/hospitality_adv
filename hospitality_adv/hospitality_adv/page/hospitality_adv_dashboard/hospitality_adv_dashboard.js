frappe.provide("hospitality_adv");

frappe.pages["hospitality-adv-dashboard"].on_page_load = function (wrapper) {
    frappe.require("/assets/hospitality_adv/css/hospitality_adv_dashboard.css");
    wrapper.hospitality_adv_dashboard = new hospitality_adv.CommandCenter(wrapper);
};

frappe.pages["hospitality-adv-dashboard"].on_page_show = function (wrapper) {
    wrapper.hospitality_adv_dashboard?.refresh();
};

hospitality_adv.CommandCenter = class CommandCenter {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.active_tab = "finance";
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: __("Hospitality ADV Command Center"),
            single_column: true,
        });
        this.page.set_primary_action(__("New Customer"), () => this.new_doc("Customer"), "add");
        this.page.set_secondary_action(__("Refresh"), () => this.refresh(), "refresh");
        this.page.add_menu_item(__("Open Insights"), () => frappe.set_route("hospitality-adv-insights"));
        this.make_layout();
        this.refresh();
    }

    make_layout() {
        this.$shell = $("<div class='had-shell' aria-live='polite'></div>").appendTo(this.page.main);
        this.$shell.on("click", ".had-tab", (event) => {
            this.active_tab = $(event.currentTarget).data("tab");
            this.render();
        });
        this.$shell.on("click", ".had-route", (event) => this.open_route(event));
        this.$shell.on("click", ".had-new", (event) => this.new_doc($(event.currentTarget).data("doctype")));
    }

    refresh() {
        this.$shell.addClass("is-loading");
        frappe.call({
            method: "hospitality_adv.dashboard.get_dashboard_data",
            callback: (response) => {
                this.data = response.message;
                this.render();
            },
            always: () => this.$shell.removeClass("is-loading"),
        });
    }

    render() {
        if (!this.data) return;
        this.$shell.html(`
            <aside class="had-left-rail">
                ${this.priority_panel()}
                ${this.kpi_panel()}
                ${this.pending_panel()}
            </aside>
            <main class="had-main-stage">
                ${this.directory_panel()}
                ${this.live_chart_panel()}
                <div class="had-bottom-grid">
                    ${this.analytics_panel()}
                    ${this.status_panel()}
                </div>
            </main>
            <aside class="had-right-rail">
                ${this.insight_panel()}
                ${this.schedule_panel()}
            </aside>
        `);
        this.render_live_charts();
    }

    priority_panel() {
        const priority =
            this.data.metrics.overdue_hospitality_tasks ||
            this.data.metrics.overdue_sales_invoices ||
            this.data.metrics.open_hospitality_tasks ||
            this.data.metrics.draft_quotations ||
            0;
        return `<section class="had-priority-panel">
            <div class="had-panel-title"><span class="had-title-mark"></span><h3>${__("Top Priorities")}</h3></div>
            <strong>${priority ? __("{0} items need attention", [priority]) : __("No open priorities")}</strong>
            <button class="had-link-button had-route" type="button" data-kind="doctype" data-target="Hospitality ADV Operation Task" data-label="${__("Operations Tasks")}">${__("View All")}</button>
        </section>`;
    }

    kpi_panel() {
        return `<section class="had-kpi-panel">
            <div class="had-panel-title"><h3>${__("Live KPIs")}</h3></div>
            <div class="had-kpi-grid">
                ${this.kpi_tile(__("Receivables"), this.data.metrics.receivables, "had-kpi-accounting", "Sales Invoice")}
                ${this.kpi_tile(__("Overdue Invoices"), this.data.metrics.overdue_sales_invoices, "had-kpi-operations", "Sales Invoice")}
            </div>
        </section>`;
    }

    kpi_tile(label, value, class_name, doctype) {
        return `<button class="had-kpi-tile had-route ${class_name}" type="button" data-kind="doctype" data-target="${this.escape(doctype)}" data-label="${this.escape(label)}" ${
            this.is_available(doctype) ? "" : "disabled"
        }>
            <span>${this.escape(label)}</span>
            <strong>${this.count(value)}</strong>
            <small>${this.is_available(doctype) ? __("Open list") : __("Unavailable")}</small>
        </button>`;
    }

    pending_panel() {
        const records = [
            ...this.data.pending.sales_invoices,
            ...this.data.pending.hospitality_tasks,
            ...this.data.pending.quotations,
        ]
            .sort((left, right) => Number(right.days_overdue || 0) - Number(left.days_overdue || 0))
            .slice(0, 5);
        const rows = records.length
            ? records.map((record) => this.pending_row(record)).join("")
            : `<div class="had-empty-state">${__("Nothing pending")}</div>`;
        return `<section class="had-pending-panel">
            <div class="had-section-head"><h3>${__("Action Queue")}</h3><button class="had-link-button had-route" type="button" data-kind="doctype" data-target="Sales Invoice" data-label="${__("Sales Invoices")}">${__("View All")}</button></div>
            <div class="had-pending-list">${rows}</div>
        </section>`;
    }

    pending_row(record) {
        return `<button class="had-pending-row had-route" type="button" data-kind="document" data-target="${this.escape(record.doctype)}" data-name="${this.escape(record.name)}" data-label="${this.escape(record.title)}">
            <span class="had-alert-dot"></span>
            <span class="had-row-copy"><strong>${this.escape(record.title)}</strong><small>${this.escape(record.name)}${record.detail ? ` - ${this.escape(record.detail)}` : ""}</small></span>
            <b>${record.amount === null || record.amount === undefined ? "" : this.money(record.amount)}</b>
        </button>`;
    }

    directory_panel() {
        return `<section class="had-directory-panel">
            <div class="had-directory-head">
                <div><div class="had-panel-title"><span class="had-module-mark"></span><h2>${__("Module Directory")}</h2></div>
                <div class="had-recent-actions">
                    ${this.new_action(__("Customer"), "Customer")}
                    ${this.new_action(__("Quotation"), "Quotation")}
                    ${this.new_action(__("Sales Invoice"), "Sales Invoice")}
                    ${this.new_action(__("Item"), "Item")}
                </div></div>
            </div>
            <div class="had-tabs" role="tablist">
                ${this.tab_button("operations", __("Operations"))}
                ${this.tab_button("finance", __("Finance"))}
                ${this.tab_button("logistics", __("Logistics"))}
                ${this.tab_button("hrms", __("Human Resources"))}
                ${this.tab_button("hospitality", __("Hospitality ADV"))}
            </div>
            <div class="had-directory-grid">${this.directory_cards()}</div>
        </section>`;
    }

    live_chart_panel() {
        const charts = this.active_charts();
        return `<section class="had-live-chart-panel">
            <div class="had-section-head">
                <div><h3>${__("Live Analysis")}</h3><span>${this.active_tab_label()}</span></div>
                <button class="had-link-button had-open-insights" type="button">${__("All insights")}</button>
            </div>
            <div class="had-tab-chart-grid">
                ${charts
                    .map(
                        (chart, index) => `<article class="had-tab-chart-card">
                            <h4>${this.escape(chart.title)}</h4>
                            <div class="had-live-chart" data-chart-index="${index}"></div>
                        </article>`
                    )
                    .join("")}
            </div>
        </section>`;
    }

    active_charts() {
        const chart_tab = {
            operations: "operations",
            finance: "finance",
            logistics: "stock",
            hrms: "hrms",
            hospitality: "hospitality",
        }[this.active_tab];
        return this.data?.charts?.[chart_tab] || [];
    }

    active_tab_label() {
        return {
            operations: __("Operations"),
            finance: __("Finance"),
            logistics: __("Stock and Logistics"),
            hrms: __("Human Resources"),
            hospitality: __("Hospitality ADV"),
        }[this.active_tab];
    }

    render_live_charts() {
        const charts = this.active_charts();
        this.$shell.find(".had-live-chart").each((index, element) => this.render_chart(element, charts[index]));
        this.$shell
            .off("click", ".had-open-insights")
            .on("click", ".had-open-insights", () => frappe.set_route("hospitality-adv-insights"));
    }

    render_chart(element, chart) {
        const values = chart?.data?.datasets?.flatMap((dataset) => dataset.values || []) || [];
        if (!chart || !values.some((value) => Number(value))) {
            $(element).html(this.zero_chart(chart));
            return;
        }

        try {
            new frappe.Chart(element, {
                data: chart.data,
                type: chart.type,
                height: 230,
                colors: chart.colors,
                axisOptions: { xIsSeries: true },
                barOptions: { spaceRatio: 0.35 },
                lineOptions: { regionFill: 1, hideDots: 0 },
                tooltipOptions: {
                    formatTooltipY: (value) => this.format_chart_value(value, chart),
                },
                valuesOverPoints: 0,
            });
        } catch (error) {
            console.error("Unable to render Hospitality ADV chart", error);
            $(element).html(this.zero_chart(chart));
        }
    }

    zero_chart(chart) {
        const labels = chart?.data?.labels || [];
        const visible_labels = labels.slice(0, 4);
        return `<div class="had-zero-state">
            <strong>0</strong>
            <span>${this.escape(chart?.empty_message || __("No records in this view."))}</span>
            <div class="had-zero-labels">${visible_labels
                .map((label) => `<span><b>0</b>${this.escape(label)}</span>`)
                .join("")}</div>
        </div>`;
    }

    format_chart_value(value, chart) {
        const numeric_value = Number(value) || 0;
        const formatted_value = new Intl.NumberFormat(undefined, {
            maximumFractionDigits: chart.value_format === "Currency" ? 2 : 0,
        }).format(numeric_value);
        const currency = frappe.boot?.sysdefaults?.currency;
        return chart.value_format === "Currency" && currency ? `${currency} ${formatted_value}` : formatted_value;
    }

    new_action(label, doctype) {
        return `<button class="had-recent-chip had-new" type="button" data-doctype="${this.escape(doctype)}" ${
            this.is_available(doctype) ? "" : "disabled"
        }>${this.escape(label)}</button>`;
    }

    tab_button(key, label) {
        return `<button class="had-tab ${this.active_tab === key ? "is-active" : ""}" type="button" role="tab" aria-selected="${
            this.active_tab === key
        }" data-tab="${key}">${label}</button>`;
    }

    directory_cards() {
        const modules = {
            operations: [
                [__("Reservations"), "Hospitality ADV Reservation"],
                [__("Room Board"), "Hospitality ADV Room"],
                [__("Guest Requests"), "Hospitality ADV Guest Message"],
                [__("Buying"), "Purchase Order"],
                [__("Selling"), "Sales Order"],
                [__("Stock"), "Stock Entry"],
            ],
            finance: [
                [__("Customers"), "Customer"],
                [__("Quotations"), "Quotation"],
                [__("Sales Invoices"), "Sales Invoice"],
                [__("Purchase Invoices"), "Purchase Invoice"],
                [__("Receivables"), "Accounts Receivable", "report"],
                [__("Payables"), "Accounts Payable", "report"],
            ],
            logistics: [
                [__("Items"), "Item"],
                [__("Warehouses"), "Warehouse"],
                [__("Material Requests"), "Material Request"],
                [__("Purchase Orders"), "Purchase Order"],
                [__("Stock Entry"), "Stock Entry"],
                [__("Stock Balance"), "Stock Balance", "report"],
            ],
            hrms: [
                [__("Employees"), "Employee"],
                [__("Attendance"), "Attendance"],
                [__("Leave Requests"), "Leave Application"],
                [__("Salary Slips"), "Salary Slip"],
                [__("Payroll"), "Payroll Entry"],
                [__("Staff Roster"), "Hospitality ADV Staff Roster"],
            ],
            hospitality: [
                [__("Properties"), "Hospitality ADV Property"],
                [__("Room Types"), "Hospitality ADV Room Type"],
                [__("Rooms"), "Hospitality ADV Room"],
                [__("Guests"), "Hospitality ADV Guest"],
                [__("Reservations"), "Hospitality ADV Reservation"],
                [__("Guest Stays"), "Hospitality ADV Guest Stay"],
                [__("Guest Messages"), "Hospitality ADV Guest Message"],
                [__("Operations Tasks"), "Hospitality ADV Operation Task"],
                [__("Housekeeping"), "Hospitality ADV Housekeeping Inspection"],
                [__("Maintenance"), "Hospitality ADV Maintenance Event"],
                [__("Hotspot Sessions"), "Hospitality ADV Hotspot Session"],
                [__("Network Flows"), "Hospitality ADV Network Flow"],
                [__("Access Events"), "Hospitality ADV Access Event"],
                [__("Guest Credentials"), "Hospitality ADV Guest Credential"],
                [__("Lift Permissions"), "Hospitality ADV Lift Permission"],
                [__("POS Outlets"), "Hospitality ADV POS Outlet"],
                [__("POS Orders"), "Hospitality ADV POS Order"],
                [__("OTA Channels"), "Hospitality ADV OTA Channel"],
                [__("Integration Events"), "Hospitality ADV Integration Event"],
            ],
        };
        return modules[this.active_tab]
            .map(([label, target, kind = "doctype"]) => this.directory_card(label, target, kind))
            .join("");
    }

    directory_card(label, target, kind) {
        const available = kind === "report" ? this.data.reports[target] : this.is_available(target);
        return `<button class="had-directory-card had-route ${available ? "" : "is-unavailable"}" type="button" data-kind="${kind}" data-target="${this.escape(target)}" data-label="${this.escape(label)}" ${
            available ? "" : "disabled"
        }>
            <span class="had-directory-icon">${this.card_mark(label)}</span>
            <strong>${this.escape(label)}</strong>
            <small>${available ? __("Open") : __("Unavailable")}</small>
        </button>`;
    }

    card_mark(label) {
        return this.escape(label.charAt(0));
    }

    analytics_panel() {
        const bars = [
            [__("Paid Sales"), this.data.metrics.paid_sales_invoices],
            [__("Overdue Sales"), this.data.metrics.overdue_sales_invoices],
            [__("Overdue Purchase"), this.data.metrics.overdue_purchase_invoices],
            [__("Overdue Tasks"), this.data.metrics.overdue_hospitality_tasks],
        ];
        const highest = Math.max(...bars.map(([, value]) => Number(value) || 0), 1);
        return `<section class="had-analytics-panel">
            <div class="had-section-head"><h3>${__("Analytics")}</h3><span>${__("Current Workload")}</span></div>
            <div class="had-bar-chart">${bars
                .map(
                    ([label, value]) => `<div class="had-bar-item"><i style="--had-value:${Math.max(
                        8,
                        ((Number(value) || 0) / highest) * 100
                    )}%"></i><strong>${this.count(value)}</strong><span>${label}</span></div>`
                )
                .join("")}</div>
        </section>`;
    }

    status_panel() {
        const statuses = [
            [__("Paid Sales Invoices"), this.data.metrics.paid_sales_invoices, "Sales Invoice"],
            [__("Overdue Sales Invoices"), this.data.metrics.overdue_sales_invoices, "Sales Invoice"],
            [__("Overdue Purchase Invoices"), this.data.metrics.overdue_purchase_invoices, "Purchase Invoice"],
            [__("Overdue Operations Tasks"), this.data.metrics.overdue_hospitality_tasks, "Hospitality ADV Operation Task"],
        ];
        return `<section class="had-status-panel">
            <div class="had-section-head"><h3>${__("System Status")}</h3><span>${__("Live")}</span></div>
            <div class="had-status-grid">${statuses
                .map(
                    ([label, value, doctype]) => `<button class="had-status-tile had-route" type="button" data-kind="doctype" data-target="${this.escape(doctype)}" data-label="${this.escape(label)}" ${
                        this.is_available(doctype) ? "" : "disabled"
                    }><strong>${this.count(value)}</strong><span>${this.escape(label)}</span></button>`
                )
                .join("")}</div>
        </section>`;
    }

    insight_panel() {
        const total = [
            this.data.metrics.overdue_sales_invoices,
            this.data.metrics.overdue_purchase_invoices,
            this.data.metrics.overdue_hospitality_tasks,
        ].reduce((sum, value) => sum + (Number(value) || 0), 0);
        return `<section class="had-insight-panel">
            <div class="had-panel-title"><span class="had-live-dot"></span><h3>${__("Operations Insight")}</h3></div>
            <div class="had-insight-score">${Math.min(100, 100 - total * 3)}<small>%</small></div>
            <span class="had-insight-caption">${__("Workflow readiness")}</span>
            <div class="had-insight-lines">
                ${this.insight_line(__("Overdue items"), total)}
                ${this.insight_line(__("Sales overdue 61+ days"), this.data.metrics.sales_overdue_61_plus)}
                ${this.insight_line(__("Active reservations"), this.data.metrics.active_reservations)}
            </div>
        </section>`;
    }

    insight_line(label, value) {
        return `<div><span>${this.escape(label)}</span><strong>${this.count(value)}</strong></div>`;
    }

    schedule_panel() {
        const entries = [
            [__("Invoice review"), this.data.pending.sales_invoices[0]?.title || __("No draft invoices")],
            [__("Quotation follow-up"), this.data.pending.quotations[0]?.title || __("No draft quotations")],
            [__("Guest operations"), this.data.pending.hospitality_tasks[0]?.title || __("No open tasks")],
        ];
        return `<section class="had-schedule-panel">
            <div class="had-panel-title"><h3>${__("Upcoming Schedule")}</h3></div>
            <div class="had-schedule-list">${entries
                .map(
                    ([label, detail]) => `<div><span class="had-schedule-dot"></span><p><strong>${this.escape(label)}</strong><small>${this.escape(detail)}</small></p></div>`
                )
                .join("")}</div>
        </section>`;
    }

    open_route(event) {
        const $target = $(event.currentTarget);
        const kind = $target.data("kind");
        const target = $target.data("target");
        if (kind === "report") frappe.set_route("query-report", target);
        else if (kind === "document") frappe.set_route("Form", target, $target.data("name"));
        else frappe.set_route("List", target);
    }

    new_doc(doctype) {
        if (!this.is_available(doctype)) {
            frappe.msgprint({
                title: __("Not available"),
                indicator: "orange",
                message: __("You do not have access to {0}, or it is not installed.", [doctype]),
            });
            return;
        }
        frappe.new_doc(doctype);
    }

    is_available(doctype) {
        return Boolean(this.data?.available?.[doctype]);
    }

    count(value) {
        return value === null || value === undefined ? "--" : new Intl.NumberFormat().format(Number(value) || 0);
    }

    money(value) {
        const amount = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(Number(value) || 0);
        const currency = frappe.boot?.sysdefaults?.currency;
        return currency ? `${currency} ${amount}` : amount;
    }

    escape(value) {
        return $("<div>").text(value || "").html();
    }
};
