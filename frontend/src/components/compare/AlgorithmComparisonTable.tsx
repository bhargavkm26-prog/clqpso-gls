import React, { useEffect, useState } from 'react';
import { ArrowUpDown, ChevronDown, ChevronUp, CheckCircle2, Zap, Activity, Info } from 'lucide-react';

export interface AlgorithmResult {
  algorithm: string;
  travel_time_min: number;
  distance_km: number;
  runtime_ms: number;
  cost?: number | null;
  iterations?: number | null;
  is_best?: boolean;
  history?: number[];
}

type SortField = 'travel_time_min' | 'distance_km' | 'runtime_ms' | null;
type SortDirection = 'asc' | 'desc';

const FALLBACK_DATA: AlgorithmResult[] = [
  {
    algorithm: 'QPSO',
    travel_time_min: 44.8,
    distance_km: 22.8,
    runtime_ms: 120.0,
    cost: 44.8,
    iterations: 100,
    is_best: true,
    history: [65.0, 55.2, 48.6, 44.8],
  },
  {
    algorithm: 'Classical PSO',
    travel_time_min: 49.2,
    distance_km: 24.5,
    runtime_ms: 95.0,
    cost: 49.2,
    iterations: 100,
    is_best: false,
    history: [68.0, 58.4, 52.1, 49.2],
  },
  {
    algorithm: 'GA (Order Crossover)',
    travel_time_min: 47.6,
    distance_km: 23.9,
    runtime_ms: 210.0,
    cost: 47.6,
    iterations: 100,
    is_best: false,
    history: [72.0, 60.1, 51.5, 47.6],
  },
  {
    algorithm: 'GA (PMX Crossover)',
    travel_time_min: 48.9,
    distance_km: 24.3,
    runtime_ms: 225.0,
    cost: 48.9,
    iterations: 100,
    is_best: false,
    history: [74.0, 62.3, 53.0, 48.9],
  },
  {
    algorithm: 'Clarke-Wright Savings',
    travel_time_min: 52.4,
    distance_km: 25.8,
    runtime_ms: 2.1,
    cost: 52.4,
    iterations: null,
    is_best: false,
    history: [52.4, 52.4, 52.4, 52.4],
  },
  {
    algorithm: 'Cheapest Insertion',
    travel_time_min: 51.0,
    distance_km: 25.1,
    runtime_ms: 2.5,
    cost: 51.0,
    iterations: null,
    is_best: false,
    history: [51.0, 51.0, 51.0, 51.0],
  },
  {
    algorithm: 'Nearest Neighbor',
    travel_time_min: 62.6,
    distance_km: 28.4,
    runtime_ms: 1.2,
    cost: 62.6,
    iterations: null,
    is_best: false,
    history: [62.6, 62.6, 62.6, 62.6],
  },
];

export default function AlgorithmComparisonTable() {
  const [data, setData] = useState<AlgorithmResult[]>(FALLBACK_DATA);
  const [loading, setLoading] = useState<boolean>(true);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>(null);
  const [sortDir, setSortDir] = useState<SortDirection>('asc');

  useEffect(() => {
    let isMounted = true;
    fetch('http://127.0.0.1:8000/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_id: 0,
        intermediate_stops: [],
        traffic_mode: 'peak',
        iterations: 100,
      }),
    })
      .then((res) => res.json())
      .then((res) => {
        if (isMounted && res.status === 'success' && Array.isArray(res.algorithms)) {
          setData(res.algorithms);
        }
      })
      .catch((err) => {
        console.warn('Backend /api/compare unavailable, using fallback data:', err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSort = (field: 'travel_time_min' | 'distance_km' | 'runtime_ms') => {
    if (sortField === field) {
      if (sortDir === 'asc') {
        setSortDir('desc');
      } else {
        setSortField(null);
        setSortDir('asc');
      }
    } else {
      setSortField(field);
      setSortDir('asc');
    }
  };

  const sortedData = [...data].sort((a, b) => {
    if (!sortField) return 0;
    const valA = a[sortField] ?? 0;
    const valB = b[sortField] ?? 0;
    return sortDir === 'asc' ? valA - valB : valB - valA;
  });

  const hasCostColumn = data.some((item) => item.cost !== undefined && item.cost !== null);

  const toggleExpand = (algo: string) => {
    setExpandedRow((prev) => (prev === algo ? null : algo));
  };

  const renderSparkline = (history: number[] | undefined, color = '#2ECC71') => {
    if (!history || history.length < 2) {
      return <span className="text-[10px] text-[#8A93A0]">Single point</span>;
    }
    const minVal = Math.min(...history);
    const maxVal = Math.max(...history);
    const range = maxVal - minVal || 1;
    const width = 140;
    const height = 36;
    const points = history
      .map((val, idx) => {
        const x = (idx / (history.length - 1)) * width;
        const y = height - ((val - minVal) / range) * (height - 8) - 4;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');

    return (
      <svg width={width} height={height} className="overflow-visible">
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
        {history.map((val, idx) => {
          const x = (idx / (history.length - 1)) * width;
          const y = height - ((val - minVal) / range) * (height - 8) - 4;
          return <circle key={idx} cx={x} cy={y} r="2.5" fill={color} />;
        })}
      </svg>
    );
  };

  return (
    <div className="bg-[#12171D] text-[#EDEFF2] rounded-xl border border-[#232B33] shadow-xl p-5 space-y-4 font-sans">
      <div className="border-b border-[#232B33] pb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div>
          <h2 className="text-lg font-bold text-[#EDEFF2] tracking-tight flex items-center gap-2">
            <Activity className="h-5 w-5 text-[#2ECC71]" />
            Algorithm Performance Comparison
          </h2>
          <p className="text-xs text-[#8A93A0] mt-0.5">
            Comparison of routing quality, computation cost, and convergence across the selected Coimbatore network scenario.
          </p>
        </div>

        <div className="flex items-center gap-3 text-[11px] text-[#8A93A0] bg-[#1A212A] px-3 py-1.5 rounded-lg border border-[#232B33]">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-[#2ECC71]"></span>
            Travel Time = Road duration
          </span>
          <span className="border-r border-[#232B33] h-3"></span>
          <span className="flex items-center gap-1">
            <Zap className="h-3 w-3 text-[#F5A623]" />
            Runtime = Algorithmic compute time
          </span>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-[#232B33] max-h-[520px] overflow-y-auto">
        <table className="w-full text-xs text-left border-collapse">
          <thead className="bg-[#161D24] text-[#8A93A0] uppercase tracking-wider font-semibold text-[11px] border-b border-[#232B33] sticky top-0 z-10">
            <tr>
              <th className="py-3 px-4 text-left">Algorithm</th>

              <th
                onClick={() => handleSort('travel_time_min')}
                className="py-3 px-4 text-right cursor-pointer hover:text-[#EDEFF2] transition-colors select-none"
              >
                <div className="flex items-center justify-end gap-1">
                  <span>Travel Time</span>
                  <ArrowUpDown className={`h-3 w-3 ${sortField === 'travel_time_min' ? 'text-[#2ECC71]' : 'opacity-40'}`} />
                </div>
              </th>

              <th
                onClick={() => handleSort('distance_km')}
                className="py-3 px-4 text-right cursor-pointer hover:text-[#EDEFF2] transition-colors select-none"
              >
                <div className="flex items-center justify-end gap-1">
                  <span>Distance</span>
                  <ArrowUpDown className={`h-3 w-3 ${sortField === 'distance_km' ? 'text-[#2ECC71]' : 'opacity-40'}`} />
                </div>
              </th>

              <th
                onClick={() => handleSort('runtime_ms')}
                className="py-3 px-4 text-right cursor-pointer hover:text-[#EDEFF2] transition-colors select-none"
              >
                <div className="flex items-center justify-end gap-1">
                  <span>Runtime</span>
                  <ArrowUpDown className={`h-3 w-3 ${sortField === 'runtime_ms' ? 'text-[#2ECC71]' : 'opacity-40'}`} />
                </div>
              </th>

              {hasCostColumn && <th className="py-3 px-4 text-right">Final Objective</th>}

              <th className="py-3 px-4 text-right">Iterations</th>
              <th className="py-3 px-4 text-center">Status</th>
              <th className="py-3 px-2 text-center w-8"></th>
            </tr>
          </thead>

          <tbody className="divide-y divide-[#232B33]">
            {sortedData.map((row) => {
              const isExpanded = expandedRow === row.algorithm;
              const isBest = row.is_best === true;

              return (
                <React.Fragment key={row.algorithm}>
                  <tr
                    onClick={() => toggleExpand(row.algorithm)}
                    className={`cursor-pointer transition-colors hover:bg-[#1A212A] ${
                      isBest ? 'bg-[#2ECC71]/10 border-l-4 border-l-[#2ECC71]' : 'bg-[#12171D]'
                    }`}
                  >
                    <td className="py-3.5 px-4 font-semibold text-[#EDEFF2] flex items-center gap-2">
                      <span>{row.algorithm}</span>
                    </td>

                    <td className="py-3.5 px-4 text-right font-mono font-medium text-[#EDEFF2]">
                      {row.travel_time_min.toFixed(1)} <span className="text-[#8A93A0] text-[10px]">min</span>
                    </td>

                    <td className="py-3.5 px-4 text-right font-mono font-medium text-[#EDEFF2]">
                      {row.distance_km.toFixed(1)} <span className="text-[#8A93A0] text-[10px]">km</span>
                    </td>

                    <td className="py-3.5 px-4 text-right font-mono font-medium text-[#EDEFF2]">
                      {row.runtime_ms < 10 ? row.runtime_ms.toFixed(1) : Math.round(row.runtime_ms)}{' '}
                      <span className="text-[#8A93A0] text-[10px]">ms</span>
                    </td>

                    {hasCostColumn && (
                      <td className="py-3.5 px-4 text-right font-mono text-[#8A93A0]">
                        {row.cost != null ? row.cost.toFixed(1) : '—'}
                      </td>
                    )}

                    <td className="py-3.5 px-4 text-right font-mono text-[#8A93A0]">
                      {row.iterations != null ? row.iterations : '—'}
                    </td>

                    <td className="py-3.5 px-4 text-center">
                      {isBest ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-[#2ECC71]/20 text-[#2ECC71] border border-[#2ECC71]/40">
                          <CheckCircle2 className="h-3 w-3" />
                          Selected / Best Result
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-medium bg-[#232B33] text-[#8A93A0]">
                          Compared
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 px-2 text-center text-[#8A93A0]">
                      {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </td>
                  </tr>

                  {isExpanded && (
                    <tr className="bg-[#161D24] border-b border-[#232B33]">
                      <td colSpan={hasCostColumn ? 8 : 7} className="p-4">
                        <div className="bg-[#12171D] p-4 rounded-lg border border-[#232B33] grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between border-b border-[#232B33] pb-2">
                              <span className="font-bold text-[#EDEFF2] text-sm">{row.algorithm} Benchmark Breakdown</span>
                              {isBest && (
                                <span className="text-[10px] font-bold text-[#2ECC71] bg-[#2ECC71]/10 px-2 py-0.5 rounded">
                                  Optimal Route
                                </span>
                              )}
                            </div>

                            <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                              <div className="bg-[#161D24] p-2.5 rounded border border-[#232B33]">
                                <span className="text-[#8A93A0] block text-[10px] uppercase font-semibold">Travel Time (On-Road)</span>
                                <span className="font-mono font-bold text-[#EDEFF2] text-sm">
                                  {row.travel_time_min.toFixed(1)} min
                                </span>
                              </div>

                              <div className="bg-[#161D24] p-2.5 rounded border border-[#232B33]">
                                <span className="text-[#8A93A0] block text-[10px] uppercase font-semibold">Distance (Length)</span>
                                <span className="font-mono font-bold text-[#EDEFF2] text-sm">
                                  {row.distance_km.toFixed(1)} km
                                </span>
                              </div>

                              <div className="bg-[#161D24] p-2.5 rounded border border-[#232B33]">
                                <span className="text-[#8A93A0] block text-[10px] uppercase font-semibold">Algorithm Runtime</span>
                                <span className="font-mono font-bold text-[#EDEFF2] text-sm">
                                  {row.runtime_ms < 10 ? row.runtime_ms.toFixed(1) : Math.round(row.runtime_ms)} ms
                                </span>
                              </div>

                              <div className="bg-[#161D24] p-2.5 rounded border border-[#232B33]">
                                <span className="text-[#8A93A0] block text-[10px] uppercase font-semibold">Iterations</span>
                                <span className="font-mono font-bold text-[#EDEFF2] text-sm">
                                  {row.iterations != null ? row.iterations : '—'}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="space-y-2 border-t md:border-t-0 md:border-l border-[#232B33] md:pl-4 pt-2 md:pt-0">
                            <span className="font-semibold text-[#EDEFF2] text-xs block">Convergence Trajectory</span>
                            <div className="bg-[#161D24] p-3 rounded border border-[#232B33] flex flex-col items-center justify-center space-y-2 min-h-[90px]">
                              {renderSparkline(row.history, isBest ? '#2ECC71' : '#F5A623')}
                              <div className="text-[10px] font-mono text-[#8A93A0] flex justify-between w-full px-2">
                                <span>History: [{row.history?.join(', ') || 'N/A'}]</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex items-start gap-2 bg-[#161D24] p-3 rounded-lg border border-[#232B33] text-[11px] text-[#8A93A0]">
        <Info className="h-4 w-4 text-[#8A93A0] shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong className="text-[#EDEFF2]">Metric Distinctions: </strong>
          <span className="text-[#EDEFF2]">Travel Time</span> is vehicle duration on road •{' '}
          <span className="text-[#EDEFF2]">Distance</span> is route length •{' '}
          <span className="text-[#EDEFF2]">Runtime</span> is algorithm computation time •{' '}
          <span className="text-[#EDEFF2]">Iterations</span> is optimization steps performed.
        </div>
      </div>
    </div>
  );
}
