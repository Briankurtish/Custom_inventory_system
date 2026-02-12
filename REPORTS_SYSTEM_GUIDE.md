# Reports & Analytics System - User Guide

## 🎯 Overview

A comprehensive Reports & Analytics system has been implemented to provide full visibility into your business performance. This system enables management to monitor financial health, track debt burden, analyze regional performance, and evaluate sales team effectiveness.

## ✨ Key Features

### 1. **Main Dashboard** (`/reports/`)
- **KPI Cards**: Total Revenue, Outstanding Debt, Collected Payments, Active Customers
- **Revenue Trend Chart**: Daily revenue visualization with interactive Chart.js graphs
- **Payment Methods Breakdown**: Pie chart showing payment method distribution
- **Top 5 Customers**: Quick view of best-performing clients
- **Revenue by Branch**: Regional performance summary
- **Top Sales Representatives**: Performance rankings
- **Quick Links**: Direct access to all detailed reports

### 2. **Client Financial Reports** (`/reports/client-financial/`)
- Complete financial overview for all customers
- **Metrics per Client**:
  - Total Revenue
  - Total Paid
  - Outstanding Debt
  - Number of Orders
  - Last Order Date
- **Advanced Filters**:
  - Search by customer name or ID
  - Filter by branch
  - Filter by debt status (With Debt, No Debt, All)
  - Sort by various metrics
- **Export**: CSV export functionality
- **Action**: Click any customer to view detailed account history

### 3. **Individual Client Detail Reports** (`/reports/client/<id>/`)
- **Personalized Account Pages** (as requested)
- Beautiful account header with customer information
- **Financial Summary Cards**: 
  - Total Invoiced
  - Total Paid
  - Outstanding Debt
  - Total Invoices
- **Monthly Trend Chart**: Historical revenue, payment, and debt tracking
- **Tabbed Interface**:
  - **Invoices Tab**: All invoices with status, amounts, and payment details
  - **Payment History Tab**: Complete payment transaction history
  - **Orders Tab**: All purchase orders history
- Full historical view of customer account activity

### 4. **Regional Performance Report** (`/reports/regional-performance/`)
- Performance metrics by branch/region (as requested)
- **Per Branch Metrics**:
  - Total Customers
  - Total Orders
  - Revenue
  - Collected Payments
  - Outstanding Debt
  - Number of Active Sales Reps
- **Interactive Chart**: Bar chart comparing revenue and debt across branches
- **Ranking System**: Branches ranked by performance
- **Date Range Filters**: Analyze any time period

### 5. **Sales Agent Performance Report** (`/reports/sales-agent-performance/`)
- Individual sales representative performance tracking (as requested)
- **Per Sales Agent Metrics**:
  - Total Customers Assigned
  - Total Orders
  - Total Revenue Generated
  - Total Collected
  - Outstanding Receivables
  - Collection Rate
- **Performance Rankings**: Gold/Silver/Bronze medals for top 3 performers
- **Filters**: By branch and date range
- Visual badges showing collection efficiency

### 6. **Financial Summary Report** (`/reports/financial-summary/`)
- Comprehensive financial analysis
- **Revenue Trend Analysis**: Daily, Weekly, or Monthly views
- **Payment Method Breakdown**: Analysis by Cash, Mobile Money, Check, Bank Deposit
- **Cash vs Credit Analysis**: Order breakdown by payment terms
- **Interactive Charts**: Multi-line trend charts with revenue, collected, and outstanding
- **Aging Analysis**: Outstanding invoices by age (0-30, 31-60, 61-90, 90+ days)

### 7. **Debt Analysis Report** (`/reports/debt-analysis/`)
- Detailed outstanding receivables analysis (as requested)
- **Summary Metrics**:
  - Total Outstanding across all clients
  - Number of Outstanding Invoices
  - Average Debt per Invoice
  - Oldest Debt (in days)
- **Top 20 Debtors**: Ranked list of customers with highest outstanding amounts
- **Outstanding Invoices Table**: 
  - Invoice details
  - Customer information
  - Days outstanding with color-coded badges
  - Outstanding amounts
- **Filters**: By branch and debt age
- Direct links to client detail pages

## 🎨 Visual Features

### Interactive Charts (Chart.js)
- **Line Charts**: Revenue trends over time
- **Bar Charts**: Regional comparisons, monthly trends
- **Doughnut/Pie Charts**: Payment method distribution
- **Multi-Dataset Charts**: Revenue vs Collected vs Outstanding

### Color-Coded Badges
- 🟢 **Green**: Good status (no debt, completed payments)
- 🟡 **Yellow/Warning**: Moderate debt (31-60 days outstanding)
- 🔴 **Red**: Critical debt (90+ days outstanding)
- 🔵 **Blue**: Informational (orders, payments)

### Responsive Design
- Works on desktop, tablet, and mobile devices
- Print-friendly layouts
- Beautiful card-based UI
- Hover effects and transitions

## 👥 Access Control

### Who Can Access Reports?
The Reports & Analytics system is restricted to management roles:
- **Director General** ✅
- **Marketing Director** ✅
- **Central Stock Manager** ✅
- **Human Resource** ✅
- **Accountant** ✅
- **Pharmacist** ✅
- **Superusers** ✅ (bypass all restrictions)

Regular workers and stock keepers cannot access these sensitive financial reports.

## 🚀 How to Use

### Accessing the System
1. Log in to the system
2. Navigate to **Reports & Analytics** in the left sidebar
3. Choose the specific report you need

### Filtering Data
Most reports include powerful filtering options:
- **Date Ranges**: Specify "From" and "To" dates
- **Branch Filter**: Analyze specific regions
- **Search**: Find specific customers or agents
- **Status Filters**: Filter by debt status, age, etc.

### Exporting Data
- **CSV Export**: Available on Client Financial Reports (more formats coming soon)
- **Print**: All reports include print-friendly layouts (use browser print function)
- **Future**: PDF and Excel exports are partially implemented

### Navigation
- **Breadcrumbs**: Navigate back to dashboard easily
- **Quick Links**: Jump between related reports
- **Direct Actions**: "View Details" buttons link to detailed pages

## 📊 Sample Use Cases

### Use Case 1: Monitor Customer Debt
1. Go to **Reports & Analytics** → **Debt Analysis**
2. View the **Top 20 Debtors** list
3. Click "View" on any customer to see their full account history
4. Check the **Payment History** tab to see what payments have been made
5. Review **Outstanding Invoices** to identify which specific invoices need collection

### Use Case 2: Evaluate Regional Performance
1. Go to **Reports & Analytics** → **Regional Performance**
2. Set your date range (e.g., last quarter)
3. Review the performance table showing all branches
4. Identify branches with high debt burden
5. Use the chart to visually compare performance

### Use Case 3: Assess Sales Team Performance
1. Go to **Reports & Analytics** → **Sales Agent Performance**
2. Set your evaluation period
3. Review the rankings to see top performers
4. Check collection rates for each sales rep
5. Identify agents who may need additional training or support

### Use Case 4: Track Individual Customer Account
1. Go to **Reports & Analytics** → **Client Financial**
2. Search for the specific customer
3. Click their name to view the detailed account page
4. Review the **Monthly Trend Chart** to see payment patterns
5. Check all invoices, payments, and orders in the tabbed interface

## 📈 Key Metrics Explained

### Revenue
- **Gross Revenue**: Total invoiced amount before taxes
- **Total Revenue**: Total invoiced amount including taxes
- **Net Collected**: Actual payments received

### Debt Metrics
- **Outstanding/Debt/Due**: Amount still owed by customers
- **Collection Rate**: (Total Paid / Total Revenue) × 100
- **Days Outstanding**: Number of days since invoice was created

### Performance Indicators
- **Active Customers**: Customers who placed orders in the selected period
- **Total Orders**: Number of purchase orders created
- **Average Debt**: Total outstanding divided by number of invoices

## 🔧 Technical Details

### Technology Stack
- **Backend**: Django 5.0 with PostgreSQL
- **Frontend**: Bootstrap 5, Chart.js 4.4.0
- **Charts**: Chart.js for interactive visualizations
- **Icons**: Font Awesome 6
- **Export**: CSV (with PDF/Excel coming soon)

### Database Models
- `SavedReport`: For saving custom report configurations
- `ReportExport`: Track report exports
- `ReportAccessLog`: Audit trail of report access

### Performance
- Optimized database queries with Django ORM aggregation
- Efficient use of `annotate()`, `aggregate()`, and `Coalesce()`
- Indexes on key fields for fast lookups
- Date-based filtering for manageable result sets

## 🎯 Upcoming Features

### Currently Pending
1. **Inventory & Product Reports**: Top-selling products, stock movement analysis
2. **Advanced Export Functionality**: Full PDF and Excel export with formatting
3. **Scheduled Reports**: Email reports automatically on a schedule
4. **Custom Report Builder**: Save custom filter combinations
5. **Report Sharing**: Share reports with specific roles

### Future Enhancements
- Real-time dashboard updates
- Predictive analytics (debt risk scoring)
- Mobile app integration
- Advanced filtering with multiple conditions
- Comparison views (year-over-year, etc.)

## ❓ FAQ

### Q: Can I export reports to Excel?
**A**: CSV export is currently available. Full Excel export with formatting is coming soon.

### Q: How often is data updated?
**A**: All reports show real-time data from the database. No caching or delays.

### Q: Can I schedule automated reports?
**A**: This feature is planned but not yet implemented. Check back in future updates.

### Q: Why can't I access the Reports section?
**A**: Reports are restricted to management roles. Contact your administrator if you believe you should have access.

### Q: Can I customize the dashboard?
**A**: Currently, the dashboard shows pre-defined KPIs. Custom dashboards are planned for future releases.

### Q: How far back can I pull historical data?
**A**: There's no limit. You can analyze data from any date range as long as the data exists in the system.

## 📞 Support

For questions or issues with the Reports & Analytics system:
1. Check this guide first
2. Contact your system administrator
3. Report bugs or request features through your normal support channels

## 🎉 Summary

The new Reports & Analytics system provides comprehensive business intelligence tools including:
- ✅ Client financial reports with debt burden tracking
- ✅ Personalized client account pages with full history
- ✅ Regional performance analysis (debt/sales by region)
- ✅ Sales agent performance tracking
- ✅ Interactive charts and visualizations
- ✅ Beautiful, modern UI with responsive design
- ✅ Role-based access control
- ✅ Export capabilities

This system gives management the tools needed to effectively monitor and control financial performance across all aspects of the business!
