import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface CacheEntry<T> {
    data: T;
    timestamp: number;
    key: string;
}

interface CacheContextType {
    getCache: <T>(key: string) => CacheEntry<T> | null;
    setCache: <T>(key: string, data: T) => void;
    clearCache: (key?: string) => void;
    isStale: (key: string, maxAge?: number) => boolean;
}

const CacheContext = createContext<CacheContextType | undefined>(undefined);

// Default cache max age: 5 minutes
const DEFAULT_MAX_AGE = 5 * 60 * 1000;

export const CacheProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [cache, setCacheState] = useState<Map<string, CacheEntry<any>>>(new Map());

    const getCache = useCallback(<T,>(key: string): CacheEntry<T> | null => {
        const entry = cache.get(key);
        return entry ? (entry as CacheEntry<T>) : null;
    }, [cache]);

    const setCache = useCallback(<T,>(key: string, data: T) => {
        setCacheState(prev => {
            const newCache = new Map(prev);
            newCache.set(key, {
                data,
                timestamp: Date.now(),
                key
            });
            return newCache;
        });
    }, []);

    const clearCache = useCallback((key?: string) => {
        if (key) {
            setCacheState(prev => {
                const newCache = new Map(prev);
                newCache.delete(key);
                return newCache;
            });
        } else {
            setCacheState(new Map());
        }
    }, []);

    const isStale = useCallback((key: string, maxAge: number = DEFAULT_MAX_AGE): boolean => {
        const entry = cache.get(key);
        if (!entry) return true;
        return Date.now() - entry.timestamp > maxAge;
    }, [cache]);

    return (
        <CacheContext.Provider value={{ getCache, setCache, clearCache, isStale }}>
            {children}
        </CacheContext.Provider>
    );
};

export const useCache = () => {
    const context = useContext(CacheContext);
    if (!context) {
        throw new Error('useCache must be used within a CacheProvider');
    }
    return context;
};
