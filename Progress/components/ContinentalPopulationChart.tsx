'use client'

import { useState } from 'react'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'

// Continental population data (1950-2023) - approximate data
const continentalData = [
  { year: 1950, asia: 1400, africa: 229, europe: 549, americas: 339, oceania: 13 },
  { year: 1960, asia: 1700, africa: 285, europe: 605, americas: 416, oceania: 16 },
  { year: 1970, asia: 2150, africa: 366, europe: 656, americas: 511, oceania: 19 },
  { year: 1980, asia: 2640, africa: 478, europe: 692, americas: 611, oceania: 23 },
  { year: 1990, asia: 3200, africa: 622, europe: 721, americas: 720, oceania: 27 },
  { year: 2000, asia: 3710, africa: 795, europe: 726, americas: 840, oceania: 31 },
  { year: 2010, asia: 4150, africa: 1020, europe: 738, americas: 940, oceania: 36 },
  { year: 2020, asia: 4600, africa: 1340, europe: 748, americas: 1000, oceania: 43 },
  { year: 2023, asia: 4700, africa: 1400, europe: 745, americas: 1020, oceania: 45 }
]

export default function ContinentalPopulationChart() {
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
            <BarChart data={continentalData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" opacity={0.6} />
              <XAxis 
                dataKey="year" 
                stroke="#64748B"
                fontSize={16}
                tickLine={false}
                axisLine={false}
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
                formatter={(value, name) => [`${value} million`, typeof name === 'string' ? name.charAt(0).toUpperCase() + name.slice(1) : name]}
                labelFormatter={(label) => `Year: ${label}`}
              />
              <Legend 
                wrapperStyle={{
                  paddingTop: '20px',
                  fontSize: '14px',
                  color: '#64748B'
                }}
              />
              <Bar dataKey="asia" stackId="a" fill="#3B82F6" name="Asia" />
              <Bar dataKey="africa" stackId="a" fill="#10B981" name="Africa" />
              <Bar dataKey="europe" stackId="a" fill="#F59E0B" name="Europe" />
              <Bar dataKey="americas" stackId="a" fill="#EF4444" name="Americas" />
              <Bar dataKey="oceania" stackId="a" fill="#8B5CF6" name="Oceania" />
            </BarChart>
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
      
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={continentalData}>
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
            fontSize={14}
            tickFormatter={(value) => `${value}M`}
            tickLine={false}
            axisLine={false}
            width={80}
            tick={{ fontSize: 12, fontWeight: 500 }}
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
            formatter={(value, name) => [`${value} million`, typeof name === 'string' ? name.charAt(0).toUpperCase() + name.slice(1) : name]}
            labelFormatter={(label) => `Year: ${label}`}
          />
          <Legend 
            wrapperStyle={{
              paddingTop: '16px',
              fontSize: '12px',
              color: '#64748B'
            }}
          />
          <Bar dataKey="asia" stackId="a" fill="#3B82F6" name="Asia" />
          <Bar dataKey="africa" stackId="a" fill="#10B981" name="Africa" />
          <Bar dataKey="europe" stackId="a" fill="#F59E0B" name="Europe" />
          <Bar dataKey="americas" stackId="a" fill="#EF4444" name="Americas" />
          <Bar dataKey="oceania" stackId="a" fill="#8B5CF6" name="Oceania" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
