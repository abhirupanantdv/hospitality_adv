frappe.provide("hospitality_adv");

frappe.pages["hospitality-adv-insights"].on_page_load = function (wrapper) {
    frappe.require("/assets/hospitality_adv/css/hospitality_adv_dashboard.css");
    wrapper.hospitality_adv_insights = new hospitality_adv.InsightsPage(wrapper);
};

frappe.pages["hospitality-adv-insights"].on_page_show = function (wrapper) {
    wrapper.hospitality_adv_insights?.refresh();
};

hospitality_adv.InsightsPage = class InsightsPage {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: __("Hospitality ADV Insights"),
            single_column: true,
        });
        this.page.set_primary_action(__("Command Center"), () => frappe.set_route("hospitality-adv-dashboard"), "home");
        this.page.set_secondary_action(__("Refresh"), () => this.refresh(), "refresh");
        this.$shell = $("<div class='had-insights-shell' aria-live='polite'></div>").appendTo(this.page.main);
        this.refresh();
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
            <header class="had-insights-header">
                <div>
                    <h2>${__("Business Insights")}</h2>
                    <p>${__("Six-month operational view")}</p>
                </div>
                <div class="had-insights-actions">
                    <button class="had-insights-action had-open-command" type="button">${__("Command Center")}</button>
                    <button class="had-insights-action had-refresh-insights" type="button">${__("Refresh")}</button>
                </div>
            </header>
            <section class="had-insights-metrics">
                ${this.metric(__("Paid sales invoices"), this.data.metrics.paid_sales_invoices, __("Submitted and fully paid"))}
                ${this.metric(__("Overdue sales invoices"), this.data.metrics.overdue_sales_invoices, __("Past due receivables"))}
                ${this.metric(__("Overdue purchase invoices"), this.data.metrics.overdue_purchase_invoices, __("Past due payables"))}
                ${this.metric(__("Overdue operations tasks"), this.data.metrics.overdue_hospitality_tasks, __("Past due tasks"))}
            </section>
            ${this.finance_section()}
            ${this.chart_section("selling", __("Selling"), __("Quotations and sales"))}
            ${this.chart_section("buying", __("Buying"), __("Purchase operations"))}
            ${this.chart_section("stock", __("Stock"), __("Inventory movements"))}
            ${this.chart_section("hrms", __("Human Resources"), __("Attendance and leave"))}
            ${this.chart_section("operations", __("Operations"), __("Reservations and task flow"))}
            ${this.chart_section("hospitality", __("Hospitality ADV"), __("Guest and POS operations"))}
        `);

        this.$shell.find(".had-insight-chart").each((index, element) => {
            const group = $(element).data("group");
            const chart = this.data.charts?.[group]?.[$(element).data("chart-index")];
            this.render_chart(element, chart);
        });
        this.$shell
            .off("click", ".had-open-command")
            .on("click", ".had-open-command", () => frappe.set_route("hospitality-adv-dashboard"));
        this.$shell.off("click", ".had-refresh-insights").on("click", ".had-refresh-insights", () => this.refresh());
        this.$shell.off("click", ".had-open-report").on("click", ".had-open-report", (event) => {
            frappe.set_route("query-report", $(event.currentTarget).data("report"));
        });
    }

    metric(label, value, detail) {
        return `<article class="had-insight-metric"><span>${this.escape(label)}</span><strong>${this.count(value)}</strong><small>${this.escape(detail)}</small></article>`;
    }

    chart_section(group, title, subtitle) {
        const charts = this.data.charts?.[group] || [];
        return `<section class="had-insight-section">
            <div class="had-insight-section-header"><h3>${this.escape(title)}</h3><span>${this.escape(subtitle)}</span></div>
            <div class="had-insight-chart-grid">
                ${charts.map((chart, index) => this.chart_card(group, chart, index)).join("")}
            </div>
        </section>`;
    }

    finance_section() {
        const charts = this.data.charts?.finance || [];
        return `<section class="had-insight-section had-finance-section">
            <div class="had-insight-section-header"><h3>${__("Finance")}</h3><span>${__("Accounting, receivables and payables")}</span></div>
            <div class="had-finance-layout">
                <div class="had-finance-charts">
                    ${charts.map((chart, index) => this.chart_card("finance", chart, index)).join("")}
                </div>
                <aside class="had-finance-reports">
                    ${this.finance_report(__("Accounts Receivable"), "Accounts Receivable", this.data.financials?.sales || {})}
                    ${this.finance_report(__("Accounts Payable"), "Accounts Payable", this.data.financials?.purchase || {})}
                </aside>
            </div>
        </section>`;
    }

    chart_card(group, chart, index) {
        return `<article class="had-insight-chart-card">
            <h4>${this.escape(chart.title)}</h4>
            <div class="had-live-chart had-insight-chart" data-group="${group}" data-chart-index="${index}"></div>
        </article>`;
    }

    finance_report(title, report, health) {
        const is_available = this.data.reports?.[report];
        return `<section class="had-finance-report-card">
            <div class="had-finance-report-head"><h4>${this.escape(title)}</h4><strong>${this.money(health.outstanding_amount)}</strong></div>
            <span>${this.count(health.outstanding_count)} ${__("open invoices")}</span>
            <div class="had-finance-list">
                ${this.finance_row(__("Overdue"), health.overdue_count, health.overdue_amount, "is-overdue")}
                ${this.finance_row(__("1-30 days"), health.age_1_30_count, health.age_1_30_amount)}
                ${this.finance_row(__("31-60 days"), health.age_31_60_count, health.age_31_60_amount)}
                ${this.finance_row(__("61+ days"), health.age_61_plus_count, health.age_61_plus_amount)}
            </div>
            <button class="had-finance-report-link had-open-report" type="button" data-report="${this.escape(report)}" ${is_available ? "" : "disabled"}>${__("Open report")}</button>
        </section>`;
    }

    finance_row(label, count, amount, class_name = "") {
        return `<div class="had-finance-row ${class_name}"><span>${this.escape(label)}</span><b>${this.count(count)}</b><strong>${this.money(amount)}</strong></div>`;
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
