'use client'

import { useState } from 'react'
import PopulationChart from '@/components/PopulationChart'
import LifeExpectancyChart from '@/components/LifeExpectancyChart'
import ContinentalPopulationChart from '@/components/ContinentalPopulationChart'

export default function HomePage() {
  const [activeTab, setActiveTab] = useState('population')

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="py-32 px-6">
        {/* Title Container - Centered */}
        <div className="max-w-5xl mx-auto text-center mb-20">
          <h1 className="elegant-title text-7xl fade-in-up">
            Progress Charts
          </h1>
        </div>
          
        {/* Clean Tab Navigation - Left Aligned within its own centered container */}
        <div className="max-w-4xl mx-auto fade-in-up-delay-1">
          <div className="flex justify-start space-x-6">
            <button
              onClick={() => setActiveTab('population')}
              className={`modern-tab ${activeTab === 'population' ? 'active' : ''}`}
            >
              Population
            </button>
            <button
              onClick={() => setActiveTab('life-expectancy')}
              className={`modern-tab ${activeTab === 'life-expectancy' ? 'active' : ''}`}
            >
              Life Expectancy
            </button>
          </div>
        </div>
      </header>

      {/* Simple empty div for spacing */}
      <div style={{height: '25px'}}></div>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 pb-16">
        {activeTab === 'population' && (
          <div className="space-y-12">
            <div className="max-w-5xl mx-auto">
              <div className="modern-card p-8 fade-in-up">
                <h3 className="elegant-title text-xl mb-4">Global Population Growth</h3>
                <div style={{height: '480px'}}>
                  <PopulationChart />
                </div>
              </div>
            </div>
            
            {/* Empty div for spacing */}
            <div style={{height: '50px'}}></div>
            
            <div className="max-w-5xl mx-auto">
              <div className="modern-card p-8 fade-in-up">
                <h3 className="elegant-title text-xl mb-4">Population by Continent</h3>
                <ContinentalPopulationChart />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'life-expectancy' && (
          <div className="max-w-5xl mx-auto">
            <div className="modern-card p-8 fade-in-up">
              <LifeExpectancyChart />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
