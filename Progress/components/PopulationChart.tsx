'use client'

import { useState } from 'react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'

// Global population data from ancient times to present (10,000 BCE - 2023)
const populationData = [
  { year: -10000, population: 1, region: 'Global' },
  { year: -8000, population: 5, region: 'Global' },
  { year: -6000, population: 10, region: 'Global' },
  { year: -4000, population: 20, region: 'Global' },
  { year: -2000, population: 27, region: 'Global' },
  { year: -1000, population: 50, region: 'Global' },
  { year: -500, population: 100, region: 'Global' },
  { year: 0, population: 170, region: 'Global' },
  { year: 500, population: 190, region: 'Global' },
  { year: 1000, population: 265, region: 'Global' },
  { year: 1200, population: 360, region: 'Global' },
  { year: 1300, population: 360, region: 'Global' },
  { year: 1400, population: 350, region: 'Global' },
  { year: 1500, population: 438, region: 'Global' },
  { year: 1600, population: 556, region: 'Global' },
  { year: 1700, population: 603, region: 'Global' },
  { year: 1750, population: 791, region: 'Global' },
  { year: 1800, population: 978, region: 'Global' },
  { year: 1850, population: 1262, region: 'Global' },
  { year: 1900, population: 1650, region: 'Global' },
  { year: 1950, population: 2536, region: 'Global' },
  { year: 1960, population: 3034, region: 'Global' },
  { year: 1970, population: 3692, region: 'Global' },
  { year: 1980, population: 4450, region: 'Global' },
  { year: 1990, population: 5327, region: 'Global' },
  { year: 2000, population: 6127, region: 'Global' },
  { year: 2010, population: 6957, region: 'Global' },
  { year: 2020, population: 7795, region: 'Global' },
  { year: 2023, population: 8000, region: 'Global' }
]

export default function PopulationChart() {
  const [isFullscreen, setIsFullscreen] = useState(false)

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  // Custom tick formatter for years
  const formatYear = (value: number) => {
    if (value < 0) {
      return `${Math.abs(value)} BCE`
    }
    return value.toString()
  }

  if (isFullscreen) {
    return (
      <div className="fullscreen-chart">
        <button 
          onClick={toggleFullscreen}
          className="close-fullscreen"
        >
          ✕ Close Fullscreen
        </button>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={populationData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" opacity={0.6} />
              <XAxis 
                dataKey="year" 
                stroke="#64748B"
                fontSize={16}
                tickFormatter={formatYear}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
              />
              <YAxis 
                stroke="#64748B"
                fontSize={18}
                tickFormatter={(value) => `${value}M`}
                tickLine={false}
                axisLine={false}
                width={80}
                tick={{ fontSize: 16, fontWeight: 500 }}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '16px',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                  padding: '16px'
                }}
                formatter={(value) => [`${value} million`, 'Population']}
                labelFormatter={(label) => `Year: ${formatYear(label)}`}
              />
              <Legend 
                wrapperStyle={{
                  paddingTop: '20px',
                  fontSize: '14px',
                  color: '#64748B'
                }}
              />
              <Line 
                type="monotone" 
                dataKey="population" 
                stroke="url(#populationGradient)" 
                strokeWidth={4}
                dot={{ fill: '#667EEA', strokeWidth: 3, r: 8, stroke: 'white' }}
                activeDot={{ r: 12, stroke: '#667EEA', strokeWidth: 4, fill: '#667EEA' }}
              />
              <defs>
                <linearGradient id="populationGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#667EEA" />
                  <stop offset="100%" stopColor="#764BA2" />
                </linearGradient>
              </defs>
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={toggleFullscreen}
        className="chart-fullscreen-btn"
        title="Fullscreen"
      >
        ⛶
      </button>
      
      <ResponsiveContainer width="100%" height={480}>
        <LineChart data={populationData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" opacity={0.6} />
          <XAxis 
            dataKey="year" 
            stroke="#64748B"
            fontSize={12}
            tickFormatter={formatYear}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis 
            stroke="#64748B"
            fontSize={16}
            tickFormatter={(value) => `${value}M`}
            tickLine={false}
            axisLine={false}
            width={80}
            tick={{ fontSize: 14, fontWeight: 500 }}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '16px',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
              padding: '12px'
            }}
            formatter={(value) => [`${value} million`, 'Population']}
            labelFormatter={(label) => `Year: ${formatYear(label)}`}
          />
          <Legend 
            wrapperStyle={{
              paddingTop: '16px',
              fontSize: '12px',
              color: '#64748B'
            }}
          />
          <Line 
            type="monotone" 
            dataKey="population" 
            stroke="url(#populationGradient)" 
            strokeWidth={3}
            dot={{ fill: '#667EEA', strokeWidth: 2, r: 6, stroke: 'white' }}
            activeDot={{ r: 8, stroke: '#667EEA', strokeWidth: 3, fill: '#667EEA' }}
          />
          <defs>
            <linearGradient id="populationGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#667EEA" />
              <stop offset="100%" stopColor="#764BA2" />
            </linearGradient>
          </defs>
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
