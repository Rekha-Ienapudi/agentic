import React from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import styles from './ChartPanel.module.css'

function OTIFChart({ data }) {
  const chartData = data.labels.map((label, i) => ({
    name: label,
    value: data.values[i],
    fill: data.values[i] >= 90 ? '#059669' : data.values[i] >= 85 ? '#D97706' : '#DC2626',
  }))

  return (
    <div className={styles.chartCard}>
      <h4 className={styles.chartTitle}>Supplier OTIF performance</h4>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={chartData} barSize={22} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
          <YAxis domain={[60, 100]} tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
          <Tooltip
            formatter={(v) => [`${v}%`, 'OTIF']}
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E7EB' }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function DelayChart({ data }) {
  const chartData = data.labels.map((label, i) => ({
    name: label,
    value: data.values[i],
    fill: i <= 1 ? '#059669' : i === 2 ? '#D97706' : '#DC2626',
  }))

  return (
    <div className={styles.chartCard}>
      <h4 className={styles.chartTitle}>Shipment delay distribution</h4>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={chartData} barSize={22} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} axisLine={false} tickLine={false} />
          <Tooltip
            formatter={(v) => [v, 'Shipments']}
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E7EB' }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function ChartPanel({ chartData }) {
  if (!chartData) return null
  return (
    <div className={styles.row}>
      <OTIFChart data={chartData.otif} />
      <DelayChart data={chartData.delays} />
    </div>
  )
}
