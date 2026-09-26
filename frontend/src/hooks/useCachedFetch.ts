import { useState, useEffect, useCallback, useRef } from 'react';
import { useCache } from '../contexts/CacheContext';

interface UseCachedFetchOptions {
    /** Cache key - if not provided, uses the URL */
    cacheKey?: string;
    /** Maximum age for cached data in milliseconds (default: 5 minutes) */
    maxAge?: number;
    /** Whether to fetch immediately on mount (default: true) */
    immediate?: boolean;
    /** Custom fetch options */
    fetchOptions?: RequestInit;
    /** Transform function for the response data */
    transform?: (data: any) => any;
    /** Automatic refresh interval in milliseconds (default: 10 minutes). Set to 0 to disable. */
    refreshInterval?: number;
}

interface UseCachedFetchResult<T> {
    data: T | null;
    loading: boolean;
    error: Error | null;
    refresh: () => Promise<void>;
    /** Whether the current data is from cache */
    isFromCache: boolean;
    /** Whether a background refresh is in progress */
    isRefreshing: boolean;
}

/**
 * Custom hook for fetching data with caching and background refresh.
 * 
 * When data is requested:
 * 1. Returns cached data immediately if available (even if stale)
 * 2. Fetches fresh data in the background
 * 3. Updates cache and UI when new data arrives
 * 4. Automatically refreshes data at the specified interval (default: 10 minutes)
 */
export function useCachedFetch<T = any>(
    url: string | null,
    options: UseCachedFetchOptions = {}
): UseCachedFetchResult<T> {
    const {
        cacheKey,
        maxAge = 5 * 60 * 1000, // 5 minutes default
        immediate = true,
        fetchOptions = {},
        transform,
        refreshInterval = 10 * 60 * 1000 // 10 minutes default
    } = options;

    const cacheContext = useCache();
    const key = cacheKey || url || '';

    // Store cache functions in refs to avoid dependency issues
    const cacheFunctionsRef = useRef(cacheContext);
    useEffect(() => {
        cacheFunctionsRef.current = cacheContext;
    }, [cacheContext]);

    // Initialize state with cached data if available
    const initialCached = (() => {
        const { getCache } = cacheContext;
        return getCache<T>(key);
    })();

    const [data, setData] = useState<T | null>(initialCached?.data ?? null);
    const [loading, setLoading] = useState(!initialCached);
    const [error, setError] = useState<Error | null>(null);
    const [isFromCache, setIsFromCache] = useState(!!initialCached);
    const [isRefreshing, setIsRefreshing] = useState(false);
    
    // Track previous values to prevent unnecessary updates
    const prevIsFromCacheRef = useRef(!!initialCached);
    const prevIsRefreshingRef = useRef(false);

    const abortControllerRef = useRef<AbortController | null>(null);
    const mountedRef = useRef(true);
    const intervalRef = useRef<number | null>(null);
    const initializedRef = useRef(false);
    const lastDataRef = useRef<string | null>(null);
    const fetchDataRef = useRef<((background: boolean) => Promise<void>) | null>(null);

    // Helper to compare data and only update if changed
    const updateDataIfChanged = useCallback((newData: T | null) => {
        const newDataStr = JSON.stringify(newData);
        if (newDataStr !== lastDataRef.current) {
            lastDataRef.current = newDataStr;
            setData(newData);
        }
    }, []);

    useEffect(() => {
        mountedRef.current = true;
        return () => {
            mountedRef.current = false;
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, []);

    const fetchData = useCallback(async (background: boolean = false) => {
        if (!url) return;

        // Cancel any ongoing request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        abortControllerRef.current = new AbortController();

        // Use ref to get latest cache functions without causing re-renders
        const { getCache, setCache, isStale } = cacheFunctionsRef.current;

        // Check cache first
        const cached = getCache<T>(key);
        const shouldUseCache = cached && !isStale(key, maxAge);

        // If we have fresh cache and this is a background refresh, skip
        if (shouldUseCache && background) {
            return;
        }

        // Set loading state (only show loading if no cached data and not background)
        if (!background && !cached) {
            setLoading(true);
        } else if (background) {
            // For background refresh, set refreshing flag
            if (!prevIsRefreshingRef.current) {
                setIsRefreshing(true);
                prevIsRefreshingRef.current = true;
            }
        } else if (cached && !background) {
            // If we have cached data and it's not background, ensure loading is false
            setLoading(false);
        }

        setError(null);

        try {
            const response = await fetch(url, {
                ...fetchOptions,
                signal: abortControllerRef.current.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const jsonData = await response.json();
            const transformedData = transform ? transform(jsonData) : jsonData;

            if (!mountedRef.current) return;

            // Update cache
            setCache(key, transformedData);

            // Update state only if data changed
            updateDataIfChanged(transformedData);
            if (prevIsFromCacheRef.current) {
                setIsFromCache(false);
                prevIsFromCacheRef.current = false;
            }
            setError(null);
        } catch (err: any) {
            if (!mountedRef.current) return;
            
            // Don't show error if it's a background refresh and we have cached data
            if (background && cached) {
                console.warn('Background refresh failed, using cached data:', err);
            } else {
                setError(err instanceof Error ? err : new Error(String(err)));
            }
        } finally {
            if (mountedRef.current) {
                setLoading(false);
                if (prevIsRefreshingRef.current) {
                    setIsRefreshing(false);
                    prevIsRefreshingRef.current = false;
                }
            }
        }
    }, [url, key, maxAge, fetchOptions, transform, updateDataIfChanged]);

    // Store fetchData in ref so it can be called from effects without being in deps
    useEffect(() => {
        fetchDataRef.current = fetchData;
    }, [fetchData]);

    const refresh = useCallback(async () => {
        await fetchData(false);
    }, [fetchData]);

    useEffect(() => {
        if (!immediate || !url) return;
        
        // Only initialize once per URL
        if (initializedRef.current) return;
        initializedRef.current = true;
        
        // Load cached data immediately if available (already done in initial state)
        const { getCache } = cacheFunctionsRef.current;
        const cached = getCache<T>(key);
        
        // If we have cached data, ensure loading is false
        if (cached) {
            setLoading(false);
        }

        // Always fetch fresh data (in background if we have cache)
        // Use setTimeout to ensure state updates are processed first
        setTimeout(() => {
            if (fetchDataRef.current) {
                fetchDataRef.current(!!cached);
            }
        }, 0);
    }, [url, immediate, key]); // Removed fetchData from deps - using ref instead

    // Set up automatic periodic refresh
    useEffect(() => {
        if (!url || refreshInterval <= 0) return;

        // Clear any existing interval
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }

        // Set up new interval to refresh data every refreshInterval
        intervalRef.current = setInterval(() => {
            if (mountedRef.current && url) {
                // Always refresh in background (don't show loading)
                // Use ref to get latest cache functions
                const { getCache, isStale } = cacheFunctionsRef.current;
                const cached = getCache<T>(key);
                const shouldUseCache = cached && !isStale(key, maxAge);
                
                // Only fetch if cache is stale
                if (!shouldUseCache) {
                    fetchData(true);
                }
            }
        }, refreshInterval);

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [url, refreshInterval, key, maxAge, fetchData]);

    return {
        data,
        loading,
        error,
        refresh,
        isFromCache,
        isRefreshing
    };
}
