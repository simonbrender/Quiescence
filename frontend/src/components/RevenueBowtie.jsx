/**
 * Revenue Architecture Bowtie Visualization
 * Based on the Celerio Revenue Architecture framework
 */
function RevenueBowtie({ company }) {
  const signals = company?.signals || {}
  const motion = signals.motion || {}
  
  // Calculate stage health based on signals
  const awarenessHealth = motion.traffic_score > 50 ? 'healthy' : 'stalled'
  const acquisitionHealth = motion.hiring_status === 'active' ? 'healthy' : 'stalled'
  const conversionHealth = motion.sales_to_eng_ratio > 0.5 && motion.sales_to_eng_ratio < 3 ? 'healthy' : 'stalled'
  const onboardingHealth = 'healthy' // Default
  const adoptionHealth = signals.market?.sentiment_score > 50 ? 'healthy' : 'stalled'
  const expansionHealth = signals.market?.github_stars > 100 ? 'healthy' : 'stalled'

  const getColor = (health) => health === 'healthy' ? '#22c55e' : '#ef4444'
  const getOpacity = (health) => health === 'healthy' ? 0.6 : 0.3

  return (
    <div className="bg-slate-800/50 border border-blue-800/30 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Revenue Architecture Bowtie</h3>
      <div className="flex flex-col items-center">
        <svg width="600" height="400" viewBox="0 0 600 400" className="w-full max-w-2xl">
          {/* Left Side - Acquisition */}
          <g>
            {/* Awareness */}
            <rect
              x="50"
              y="50"
              width="80"
              height="40"
              rx="5"
              fill={getColor(awarenessHealth)}
              opacity={getOpacity(awarenessHealth)}
              stroke={getColor(awarenessHealth)}
              strokeWidth="2"
            />
            <text x="90" y="75" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
              Awareness
            </text>

            {/* MQL */}
            <rect
              x="50"
              y="110"
              width="80"
              height="40"
              rx="5"
              fill={getColor(acquisitionHealth)}
              opacity={getOpacity(acquisitionHealth)}
              stroke={getColor(acquisitionHealth)}
              strokeWidth="2"
            />
            <text x="90" y="135" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
              MQL
            </text>

            {/* SQL */}
            <rect
              x="50"
              y="170"
              width="80"
              height="40"
              rx="5"
              fill={getColor(acquisitionHealth)}
              opacity={getOpacity(acquisitionHealth)}
              stroke={getColor(acquisitionHealth)}
              strokeWidth="2"
            />
            <text x="90" y="195" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
              SQL
            </text>

            {/* Opportunity */}
            <rect
              x="50"
              y="230"
              width="80"
              height="40"
              rx="5"
              fill={getColor(conversionHealth)}
              opacity={getOpacity(conversionHealth)}
              stroke={getColor(conversionHealth)}
              strokeWidth="2"
            />
            <text x="90" y="255" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
              Opportunity
            </text>

            {/* Closed Won */}
            <rect
              x="50"
              y="290"
              width="80"
              height="40"
              rx="5"
              fill={getColor(conversionHealth)}
              opacity={getOpacity(conversionHealth)}
              stroke={getColor(conversionHealth)}
              strokeWidth="2"
            />
            <text x="90" y="315" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
              Closed Won
            </text>

            {/* Arrows Left */}
            <line x1="130" y1="70" x2="200" y2="70" stroke="#3b82f6" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <line x1="130" y1="130" x2="200" y2="130" stroke="#3b82f6" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <line x1="130" y1="190" x2="200" y2="190" stroke="#3b82f6" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <line x1="130" y1="250" x2="200" y2="250" stroke="#3b82f6" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <line x1="130" y1="310" x2="200" y2="310" stroke="#3b82f6" strokeWidth="2" markerEnd="url(#arrowhead)" />
          </g>

          {/* Center - Customer */}
          <circle
            cx="300"
            cy="200"
            r="60"
            fill="#1e40af"
            opacity="0.8"
            stroke="#3b82f6"
            strokeWidth="3"
          />
          <text x="300" y="200" textAnchor="middle" fill="white" fontSize="16" fontWeight="bold">
            Customer
          </text>

          {/* Right Side - Expansion */}
          <g>
            {/* Onboarding */}
            <rect
              x="470"
              y="50"
              width="80"
              height="40"
              rx="5"
              fill={getColor(onboardingHealth)}
              opacity={getOpacity(onboardingHealth)}
              stroke={getColor(onboardingHealth)}
              strokeWidth="2"
            />
            <text x="510" y="75" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
              Onboarding
            </text>

            {/* Adoption */}
            <rect
              x="470"
              y="110"
              width="80"
              height="40"
              rx="5"
              fill={getColor(adoptionHealth)}
              opacity={getOpacity(adoptionHealth)}
              stroke={getColor(adoptionHealth)}
              strokeWidth="2"
            />
            <text x="510" y="135" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
              Adoption
            </text>

            {/* Value Realization */}
            <rect
              x="470"
              y="170"
              width="80"
              height="40"
              rx="5"
              fill={getColor(adoptionHealth)}
              opacity={getOpacity(adoptionHealth)}
              stroke={getColor(adoptionHealth)}
              strokeWidth="2"
            />
            <text x="510" y="195" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
              Value Real
            </text>

            {/* Expansion */}
            <rect
              x="470"
              y="230"
              width="80"
              height="40"
              rx="5"
              fill={getColor(expansionHealth)}
              opacity={getOpacity(expansionHealth)}
              stroke={getColor(expansionHealth)}
              strokeWidth="2"
            />
            <text x="510" y="255" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
              Expansion
            </text>

            {/* Renewal */}
            <rect
              x="470"
              y="290"
              width="80"
              height="40"
              rx="5"
              fill={getColor(expansionHealth)}
              opacity={getOpacity(expansionHealth)}
              stroke={getColor(expansionHealth)}
              strokeWidth="2"
            />
            <text x="510" y="315" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
              Renewal
            </text>

            {/* Arrows Right */}
            <line x1="400" y1="70" x2="470" y2="70" stroke="#3b82f6" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <line x1="400" y1="130" x2="470" y2="130" stroke="#3b82f6" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <line x1="400" y1="190" x2="470" y2="190" stroke="#3b82f6" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <line x1="400" y1="250" x2="470" y2="250" stroke="#3b82f6" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <line x1="400" y1="310" x2="470" y2="310" stroke="#3b82f6" strokeWidth="2" markerEnd="url(#arrowhead)" />
          </g>

          {/* Arrow marker definition */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#3b82f6" />
            </marker>
          </defs>
        </svg>

        <div className="mt-4 flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span className="text-slate-300">Healthy</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span className="text-slate-300">Stalled</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RevenueBowtie

