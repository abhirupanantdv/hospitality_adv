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
        this.active_tab = "overview";
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: __("Hospitality ADV"),
            single_column: true,
        });
        this.page.set_primary_action(__("New Customer"), () => this.new_doc("Customer"), "add");
        this.page.set_secondary_action(__("Refresh"), () => this.refresh(), "refresh");
        this.make_layout();
        this.refresh();
    }

    make_layout() {
        this.$body = $(
            `<div class="hospitality-adv-dashboard">
                <div class="had-metrics" aria-live="polite"></div>
                <div class="had-tabs" role="tablist">
                    ${this.tab_button("overview", __("Overview"))}
                    ${this.tab_button("accounting", __("Accounting"))}
                    ${this.tab_button("buying", __("Buying"))}
                    ${this.tab_button("selling", __("Selling"))}
                    ${this.tab_button("stock", __("Stock"))}
                    ${this.tab_button("hrms", __("HRMS"))}
                    ${this.tab_button("hospitality", __("Hospitality ADV"))}
                </div>
                <div class="had-content"></div>
            </div>`
        ).appendTo(this.page.main);

        this.$body.on("click", ".had-tab", (event) => {
            this.active_tab = $(event.currentTarget).data("tab");
            this.render();
        });
        this.$body.on("click", ".had-route", (event) => this.open_route(event));
        this.$body.on("click", ".had-new", (event) => this.new_doc($(event.currentTarget).data("doctype")));
    }

    tab_button(key, label) {
        return `<button class="had-tab" type="button" role="tab" data-tab="${key}">${label}</button>`;
    }

    refresh() {
        this.$body?.addClass("is-loading");
        frappe.call({
            method: "hospitality_adv.dashboard.get_dashboard_data",
            callback: (response) => {
                this.data = response.message;
                this.render();
            },
            always: () => this.$body?.removeClass("is-loading"),
        });
    }

    render() {
        if (!this.data) {
            return;
        }
        this.render_metrics();
        this.$body.find(".had-tab").attr("aria-selected", "false").removeClass("is-active");
        this.$body
            .find(`.had-tab[data-tab="${this.active_tab}"]`)
            .attr("aria-selected", "true")
            .addClass("is-active");
        this.$body.find(".had-content").html(this.render_tab());
    }

    render_metrics() {
        const metrics = [
            ["customers", __("Customers"), "Customer"],
            ["draft_quotations", __("Pending Quotations"), "Quotation"],
            ["receivables", __("Receivables"), "Sales Invoice"],
            ["payables", __("Payables"), "Purchase Invoice"],
            ["stock_items", __("Stock Items"), "Item"],
            ["active_reservations", __("Active Reservations"), "Hospitality ADV Reservation"],
        ];
        this.$body.find(".had-metrics").html(
            metrics
                .map(([key, label, doctype]) => this.metric_card(label, this.data.metrics[key], doctype))
                .join("")
        );
    }

    metric_card(label, value, doctype) {
        const unavailable = !this.is_available(doctype);
        return `<button class="had-metric had-route ${unavailable ? "is-unavailable" : ""}" type="button"
            data-kind="doctype" data-target="${this.escape(doctype)}" data-label="${this.escape(label)}" ${
                unavailable ? "disabled" : ""
            }>
            <span>${this.escape(label)}</span>
            <strong>${value === null || value === undefined ? "--" : frappe.format(value, { fieldtype: "Int" })}</strong>
        </button>`;
    }

    render_tab() {
        const tabs = {
            overview: () => this.overview(),
            accounting: () => this.module_tab("accounting"),
            buying: () => this.module_tab("buying"),
            selling: () => this.module_tab("selling"),
            stock: () => this.module_tab("stock"),
            hrms: () => this.module_tab("hrms"),
            hospitality: () => this.module_tab("hospitality"),
        };
        return tabs[this.active_tab]();
    }

    overview() {
        return `<div class="had-overview">
            <section class="had-panel had-quick-actions">
                <div class="had-section-heading"><h3>${__("Create")}</h3></div>
                <div class="had-command-grid">
                    ${this.new_button(__("Customer"), "Customer")}
                    ${this.new_button(__("Item"), "Item")}
                    ${this.new_button(__("Quotation"), "Quotation")}
                    ${this.new_button(__("Sales Invoice"), "Sales Invoice")}
                    ${this.new_button(__("Purchase Order"), "Purchase Order")}
                    ${this.new_button(__("Reservation"), "Hospitality ADV Reservation")}
                </div>
            </section>
            <div class="had-work-grid">
                ${this.pending_panel(__("Pending Quotations"), this.data.pending.quotations)}
                ${this.pending_panel(__("Pending Sales Invoices"), this.data.pending.sales_invoices)}
                ${this.pending_panel(__("Open Hospitality Tasks"), this.data.pending.hospitality_tasks)}
            </div>
            <section class="had-panel had-shortcuts">
                <div class="had-section-heading"><h3>${__("Core Workflows")}</h3></div>
                <div class="had-command-grid">
                    ${this.route_button(__("Buying"), "doctype", "Purchase Order", "Purchase Order")}
                    ${this.route_button(__("Selling"), "doctype", "Sales Order", "Sales Order")}
                    ${this.route_button(__("Stock"), "doctype", "Stock Entry", "Stock Entry")}
                    ${this.route_button(__("HRMS"), "doctype", "Employee", "Employee")}
                    ${this.route_button(__("Hospitality ADV"), "doctype", "Hospitality ADV Room", "Hospitality ADV Room")}
                </div>
            </section>
        </div>`;
    }

    module_tab(module) {
        const definitions = {
            accounting: {
                title: __("Accounting"),
                metrics: [
                    ["receivables", __("Receivable Invoices"), "Sales Invoice"],
                    ["payables", __("Payable Invoices"), "Purchase Invoice"],
                ],
                docs: ["Customer", "Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry"],
                reports: ["Accounts Receivable", "Accounts Payable", "Balance Sheet", "Profit and Loss Statement", "General Ledger"],
            },
            buying: {
                title: __("Buying"),
                metrics: [["open_purchase_orders", __("Submitted Purchase Orders"), "Purchase Order"]],
                docs: ["Supplier", "Material Request", "Request for Quotation", "Supplier Quotation", "Purchase Order", "Purchase Invoice"],
                reports: ["Accounts Payable"],
            },
            selling: {
                title: __("Selling"),
                metrics: [["draft_quotations", __("Pending Quotations"), "Quotation"]],
                docs: ["Customer", "Quotation", "Sales Order", "Delivery Note", "Sales Invoice", "Payment Entry"],
                reports: ["Sales Analytics", "Accounts Receivable"],
            },
            stock: {
                title: __("Stock"),
                metrics: [["stock_items", __("Active Items"), "Item"]],
                docs: ["Item", "Item Group", "Warehouse", "Material Request", "Stock Entry", "Delivery Note"],
                reports: ["Stock Balance", "Stock Ledger"],
            },
            hrms: {
                title: __("HRMS"),
                metrics: [
                    ["active_employees", __("Active Employees"), "Employee"],
                    ["open_leave_requests", __("Open Leave Requests"), "Leave Application"],
                ],
                docs: ["Employee", "Attendance", "Leave Application", "Salary Slip", "Payroll Entry"],
                reports: [],
            },
            hospitality: {
                title: __("Hospitality ADV"),
                metrics: [
                    ["active_reservations", __("Active Reservations"), "Hospitality ADV Reservation"],
                    ["open_hospitality_tasks", __("Open Tasks"), "Hospitality ADV Operation Task"],
                ],
                docs: [
                    "Hospitality ADV Property",
                    "Hospitality ADV Room Type",
                    "Hospitality ADV Room",
                    "Hospitality ADV Guest",
                    "Hospitality ADV Reservation",
                    "Hospitality ADV Guest Stay",
                    "Hospitality ADV Guest Message",
                    "Hospitality ADV Operation Task",
                    "Hospitality ADV Housekeeping Inspection",
                    "Hospitality ADV Maintenance Event",
                    "Hospitality ADV Hotspot Session",
                    "Hospitality ADV Network Flow",
                    "Hospitality ADV Access Event",
                    "Hospitality ADV Guest Credential",
                    "Hospitality ADV Lift Permission",
                    "Hospitality ADV POS Outlet",
                    "Hospitality ADV POS Order",
                    "Hospitality ADV Staff Roster",
                    "Hospitality ADV OTA Channel",
                    "Hospitality ADV Integration Event",
                ],
                reports: [],
            },
        };
        const definition = definitions[module];
        return `<div class="had-module">
            <section class="had-module-header">
                <h2>${definition.title}</h2>
                <div class="had-inline-metrics">
                    ${definition.metrics.map(([key, label, doctype]) => this.metric_card(label, this.data.metrics[key], doctype)).join("")}
                </div>
            </section>
            <section class="had-panel">
                <div class="had-section-heading"><h3>${__("Documents")}</h3></div>
                <div class="had-command-grid">
                    ${definition.docs.map((doctype) => this.route_button(doctype, "doctype", doctype, doctype)).join("")}
                </div>
            </section>
            ${definition.reports.length ? this.report_panel(definition.reports) : ""}
            ${module === "accounting" ? this.pending_panel(__("Pending Purchase Invoices"), this.data.pending.purchase_invoices) : ""}
        </div>`;
    }

    report_panel(reports) {
        return `<section class="had-panel">
            <div class="had-section-heading"><h3>${__("Reports")}</h3></div>
            <div class="had-command-grid">
                ${reports.map((report) => this.route_button(report, "report", report, report)).join("")}
            </div>
        </section>`;
    }

    pending_panel(title, records) {
        const content = records.length
            ? records
                  .map(
                      (record) => `<button type="button" class="had-list-row had-route" data-kind="document"
                            data-target="${this.escape(record.doctype)}" data-name="${this.escape(record.name)}"
                            data-label="${this.escape(record.title)}">
                            <span><strong>${this.escape(record.title)}</strong><small>${this.escape(record.status || record.name)}</small></span>
                            <b>${record.amount === null || record.amount === undefined ? "" : frappe.format(record.amount, { fieldtype: "Currency" })}</b>
                        </button>`
                  )
                  .join("")
            : `<div class="had-empty-state">${__("Nothing pending")}</div>`;
        return `<section class="had-panel had-pending-panel">
            <div class="had-section-heading"><h3>${title}</h3></div>
            <div class="had-list">${content}</div>
        </section>`;
    }

    new_button(label, doctype) {
        const unavailable = !this.is_available(doctype);
        return `<button class="had-command had-new ${unavailable ? "is-unavailable" : ""}" type="button"
            data-doctype="${this.escape(doctype)}" ${unavailable ? "disabled" : ""}>
            <span>${this.escape(label)}</span><small>${__("New")}</small>
        </button>`;
    }

    route_button(label, kind, target, doctype) {
        const available = kind === "report" ? this.data.reports[target] : this.is_available(doctype);
        return `<button class="had-command had-route ${available ? "" : "is-unavailable"}" type="button"
            data-kind="${kind}" data-target="${this.escape(target)}" data-label="${this.escape(label)}" ${
                available ? "" : "disabled"
            }>
            <span>${this.escape(label)}</span><small>${available ? __("Open") : __("Unavailable")}</small>
        </button>`;
    }

    open_route(event) {
        const $target = $(event.currentTarget);
        const kind = $target.data("kind");
        const target = $target.data("target");
        if (kind === "report") {
            frappe.set_route("query-report", target);
        } else if (kind === "document") {
            frappe.set_route("Form", target, $target.data("name"));
        } else {
            frappe.set_route("List", target);
        }
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

    escape(value) {
        return $("<div>").text(value || "").html();
    }
};
