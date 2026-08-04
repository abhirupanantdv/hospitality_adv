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
            ${this.chart_section("finance", __("Finance"), __("Accounting"))}
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
    }

    metric(label, value, detail) {
        return `<article class="had-insight-metric"><span>${this.escape(label)}</span><strong>${this.count(value)}</strong><small>${this.escape(detail)}</small></article>`;
    }

    chart_section(group, title, subtitle) {
        const charts = this.data.charts?.[group] || [];
        return `<section class="had-insight-section">
            <div class="had-insight-section-header"><h3>${this.escape(title)}</h3><span>${this.escape(subtitle)}</span></div>
            <div class="had-insight-chart-grid">
                ${charts
                    .map(
                        (chart, index) => `<article class="had-insight-chart-card">
                            <h4>${this.escape(chart.title)}</h4>
                            <div class="had-live-chart had-insight-chart" data-group="${group}" data-chart-index="${index}"></div>
                        </article>`
                    )
                    .join("")}
            </div>
        </section>`;
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
        return value === null || value === undefined ? "--" : frappe.format(value, { fieldtype: "Int" });
    }

    escape(value) {
        return $("<div>").text(value || "").html();
    }
};
