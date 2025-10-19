import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  TicketIcon,
  BookOpenIcon,
  EnvelopeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';

const stats = [
  { name: 'Total Tickets', value: '124', icon: TicketIcon, change: '+12%', changeType: 'increase' },
  { name: 'Resolved Today', value: '18', icon: CheckCircleIcon, change: '+8%', changeType: 'increase' },
  { name: 'KB Articles', value: '342', icon: BookOpenIcon, change: '+2%', changeType: 'increase' },
  { name: 'Emails Processed', value: '89', icon: EnvelopeIcon, change: '+15%', changeType: 'increase' },
];

const recentActivity = [
  {
    id: 1,
    type: 'ticket_created',
    title: 'New ticket: Login issues with SSO',
    time: '2 minutes ago',
    status: 'pending',
  },
  {
    id: 2,
    type: 'email_sent',
    title: 'Auto-response sent for password reset',
    time: '5 minutes ago',
    status: 'completed',
  },
  {
    id: 3,
    type: 'kb_search',
    title: 'Knowledge base search: API documentation',
    time: '8 minutes ago',
    status: 'completed',
  },
  {
    id: 4,
    type: 'ticket_resolved',
    title: 'Ticket resolved: Email configuration',
    time: '12 minutes ago',
    status: 'completed',
  },
];

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

export default function Dashboard() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await apiService.healthCheck();
        setHealthStatus(response.data);
      } catch (error) {
        console.error('Health check failed:', error);
        setHealthStatus({ status: 'unhealthy', error: error.message });
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-700">
          Welcome to SuperTickets.AI - Your AI-powered support triage system
        </p>
      </div>

      {/* Health Status */}
      <div className="mb-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {loading ? (
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
                ) : healthStatus?.status === 'healthy' ? (
                  <CheckCircleIcon className="h-6 w-6 text-green-400" />
                ) : (
                  <ExclamationTriangleIcon className="h-6 w-6 text-red-400" />
                )}
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">System Status</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {loading ? 'Checking...' : healthStatus?.status || 'Unknown'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((item) => (
          <div key={item.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <item.icon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">{item.name}</dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-gray-900">{item.value}</div>
                      <div
                        className={classNames(
                          item.changeType === 'increase' ? 'text-green-600' : 'text-red-600',
                          'ml-2 flex items-baseline text-sm font-semibold'
                        )}
                      >
                        {item.change}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Recent Activity</h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Latest system activities and processed requests
          </p>
        </div>
        <ul className="divide-y divide-gray-200">
          {recentActivity.map((activity) => (
            <li key={activity.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div
                        className={classNames(
                          activity.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800',
                          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium'
                        )}
                      >
                        {activity.status}
                      </div>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                      <p className="text-sm text-gray-500">{activity.time}</p>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <ChartBarIcon className="h-5 w-5 text-gray-400" />
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}