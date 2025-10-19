import React, { useState } from 'react';
import { MagnifyingGlassIcon, BookOpenIcon } from '@heroicons/react/24/outline';
import { apiService } from '../services/api';

export default function KnowledgeBase() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiService.searchKnowledgeBase(searchQuery, 10);
      setSearchResults(response.data.results || []);
    } catch (err) {
      setError('Failed to search knowledge base. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Knowledge Base</h1>
        <p className="mt-2 text-sm text-gray-700">
          Search through your knowledge base for solutions and documentation
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white shadow sm:rounded-lg mb-6">
        <div className="px-4 py-5 sm:p-6">
          <form onSubmit={handleSearch}>
            <div className="flex rounded-md shadow-sm">
              <div className="relative flex-grow focus-within:z-10">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="focus:ring-indigo-500 focus:border-indigo-500 block w-full rounded-none rounded-l-md pl-10 sm:text-sm border-gray-300"
                  placeholder="Search knowledge base..."
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="-ml-px relative inline-flex items-center space-x-2 px-4 py-2 border border-gray-300 text-sm font-medium rounded-r-md text-gray-700 bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
                ) : (
                  <MagnifyingGlassIcon className="h-4 w-4" />
                )}
                <span>Search</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Search Results ({searchResults.length})
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Found {searchResults.length} relevant articles
            </p>
          </div>
          <ul className="divide-y divide-gray-200">
            {searchResults.map((result, index) => (
              <li key={index}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <BookOpenIcon className="h-6 w-6 text-gray-400" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-900">
                          {result.title || 'Knowledge Base Article'}
                        </p>
                        <p className="text-sm text-gray-500">
                          {result.content || result.summary || 'No preview available'}
                        </p>
                        {result.similarity && (
                          <p className="text-xs text-gray-400 mt-1">
                            Similarity: {(result.similarity * 100).toFixed(1)}%
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex-shrink-0">
                      <button className="text-indigo-600 hover:text-indigo-900 text-sm font-medium">
                        View
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Empty State */}
      {!loading && searchResults.length === 0 && searchQuery && !error && (
        <div className="text-center py-12">
          <BookOpenIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search terms or check the spelling.
          </p>
        </div>
      )}

      {/* Initial State */}
      {!searchQuery && (
        <div className="text-center py-12">
          <BookOpenIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Search Knowledge Base</h3>
          <p className="mt-1 text-sm text-gray-500">
            Enter a search term above to find relevant articles and solutions.
          </p>
        </div>
      )}
    </div>
  );
}