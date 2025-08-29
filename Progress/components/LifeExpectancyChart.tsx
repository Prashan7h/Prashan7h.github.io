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

// Global life expectancy data (1950-2023)
const lifeExpectancyData = [
  { year: 1950, lifeExpectancy: 48, region: 'Global' },
  { year: 1960, lifeExpectancy: 52, region: 'Global' },
  { year: 1970, lifeExpectancy: 58, region: 'Global' },
  { year: 1980, lifeExpectancy: 62, region: 'Global' },
  { year: 1990, lifeExpectancy: 65, region: 'Global' },
  { year: 2000, lifeExpectancy: 67, region: 'Global' },
  { year: 2010, lifeExpectancy: 70, region: 'Global' },
  { year: 2020, lifeExpectancy: 73, region: 'Global' },
  { year: 2023, lifeExpectancy: 73, region: 'Global' }
]

export default function LifeExpectancyChart() {
  const [isFullscreen, setIsFullscreen] = useState(false)

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
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
            <LineChart data={lifeExpectancyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" opacity={0.6} />
              <XAxis 
                dataKey="year" 
                stroke="#64748B"
                fontSize={16}
                tickFormatter={(value) => value.toString()}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                stroke="#64748B"
                fontSize={16}
                tickFormatter={(value) => `${value}y`}
                tickLine={false}
                axisLine={false}
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
                formatter={(value) => [`${value} years`, 'Life Expectancy']}
                labelFormatter={(label) => `Year: ${label}`}
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
                dataKey="lifeExpectancy" 
                stroke="url(#lifeExpectancyGradient)" 
                strokeWidth={4}
                dot={{ fill: '#10B981', strokeWidth: 3, r: 8, stroke: 'white' }}
                activeDot={{ r: 12, stroke: '#10B981', strokeWidth: 4, fill: '#10B981' }}
              />
              <defs>
                <linearGradient id="lifeExpectancyGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#10B981" />
                  <stop offset="100%" stopColor="#059669" />
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
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={lifeExpectancyData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" opacity={0.6} />
          <XAxis 
            dataKey="year" 
            stroke="#64748B"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis 
            stroke="#64748B"
            fontSize={12}
            tickFormatter={(value) => `${value}y`}
            tickLine={false}
            axisLine={false}
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
            formatter={(value) => [`${value} years`, 'Life Expectancy']}
            labelFormatter={(label) => `Year: ${label}`}
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
            dataKey="lifeExpectancy" 
            stroke="url(#lifeExpectancyGradient)" 
            strokeWidth={3}
            dot={{ fill: '#10B981', strokeWidth: 2, r: 6, stroke: 'white' }}
            activeDot={{ r: 8, stroke: '#10B981', strokeWidth: 3, fill: '#10B981' }}
          />
          <defs>
            <linearGradient id="lifeExpectancyGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#10B981" />
              <stop offset="100%" stopColor="#059669" />
            </linearGradient>
          </defs>
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
