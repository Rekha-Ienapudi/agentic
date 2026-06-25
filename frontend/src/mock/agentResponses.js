/**
 * Realistic mock responses for the demo.
 * Replace with real API data when backend is connected.
 */

export const MOCK_RESPONSE = {
  conversationId: 'conv-001',
  kpis: {
    otif: { value: '87.4%', delta: '−2.1% vs last month', trend: 'down' },
    ordersAtRisk: { value: '47', delta: '+12 this week', trend: 'down' },
    revenueExposure: { value: '€4.2M', delta: '3 critical suppliers', trend: 'down' },
    inventoryHealth: { value: '73%', delta: '2 stockout risks', trend: 'neutral' },
  },
  executiveBrief: {
    summary:
      'Your supply chain is currently under moderate-to-high stress. The primary driver is a confirmed 14-day production delay at Foxconn (Shenzhen), affecting 12 critical materials across 3 plants. Prague is the most exposed site at 91% capacity utilisation. Two additional APAC suppliers show elevated risk scores (>70).',
    metrics: [
      { value: '87.4%', label: 'OTIF' },
      { value: '€4.2M', label: 'Revenue at risk', highlight: true },
      { value: '3', label: 'Plants affected' },
      { value: '47', label: 'Orders at risk' },
    ],
    recommendation:
      'Recommended escalation: activate alternative supplier for Material Y within 48 hours; reroute 18 priority customer orders to Munich plant.',
  },
  risks: [
    {
      id: 'r1',
      severity: 'critical',
      title: 'Foxconn delay — 12 materials affected',
      detail: '14 days · 47 customer orders impacted · revenue risk €4.2M',
    },
    {
      id: 'r2',
      severity: 'critical',
      title: 'Material Y stockout in 3 days',
      detail: 'Plant Prague · safety stock breached · daily consumption 240 units',
    },
    {
      id: 'r3',
      severity: 'high',
      title: 'Supplier X — OTIF only 82%',
      detail: 'Electronics category · 6 open POs at risk · 3rd consecutive month below SLA',
    },
    {
      id: 'r4',
      severity: 'medium',
      title: 'Prague plant at 91% capacity',
      detail: 'Risk of fulfilment bottleneck if rerouting from Munich is delayed',
    },
  ],
  actions: [
    {
      id: 'a1',
      title: 'Activate alternative supplier for Material Y',
      detail: 'Supplier B · qualified · +8% cost delta · 5-day lead time',
    },
    {
      id: 'a2',
      title: 'Reroute 18 priority orders to Munich plant',
      detail: 'Frees Prague capacity · covers all premium customers',
    },
    {
      id: 'a3',
      title: 'Arrange air freight for critical shipments',
      detail: 'Est. cost €42K · protects €380K revenue at risk',
    },
    {
      id: 'a4',
      title: 'Escalate Supplier X performance review',
      detail: 'OTIF below 90% threshold for 3 consecutive months · initiate SLA discussion',
    },
  ],
  followUps: [
    'Which customer orders are affected by the Foxconn delay?',
    'What are the alternative suppliers for Material Y?',
    'What is the cost vs revenue saved for air freight?',
    'Which plants are most affected by current disruptions?',
    'Create an executive summary for the COO.',
  ],
  chartData: {
    otif: {
      labels: ['Foxconn', 'Supplier B', 'Supplier C', 'Supplier X', 'Supplier E'],
      values: [78, 95, 91, 82, 88],
    },
    delays: {
      labels: ['0–3 d', '4–7 d', '8–14 d', '15–21 d', '>21 d'],
      values: [42, 28, 18, 9, 3],
    },
  },
  alertsBanner: '3 active disruptions · Foxconn: 14-day delay · Material Y: stockout in 3 days · Prague plant: 91% capacity',
}

export const PREVIOUS_CONVERSATIONS = [
  {
    id: 'conv-001',
    title: 'Foxconn delay impact analysis',
    preview: '47 orders at risk · €4.2M revenue exposure',
    timestamp: 'Today 09:14',
    query: 'Supplier Foxconn reports a delay of 14 days. What does this mean for us?',
  },
  {
    id: 'conv-002',
    title: 'Supplier risk review — APAC region',
    preview: '3 critical suppliers flagged',
    timestamp: 'Yesterday 14:32',
    query: 'Which suppliers currently have the highest risk score?',
  },
  {
    id: 'conv-003',
    title: 'Stockout risk — next 7 days',
    preview: 'Material Y: 3 days remaining stock',
    timestamp: 'Mon 11:05',
    query: 'Where is a stockout risk imminent in the next 7 days?',
  },
]
