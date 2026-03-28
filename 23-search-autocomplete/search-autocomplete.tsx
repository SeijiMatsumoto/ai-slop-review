// AI-generated PR — review this code
// Description: Added search autocomplete component with debounced API calls
// Provides a type-ahead search experience with highlighted matching text
// and keyboard navigation support.

import React, { useState, useEffect, useRef, useCallback } from "react";

interface SearchResult {
  id: string;
  title: string;
  highlightedTitle: string;
  category: string;
}

interface SearchAutocompleteProps {
  apiEndpoint: string;
  placeholder?: string;
  onSelect: (result: SearchResult) => void;
  debounceMs?: number;
}

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

export default function SearchAutocomplete({
  apiEndpoint,
  placeholder = "Search...",
  onSelect,
  debounceMs = 300,
}: SearchAutocompleteProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const debouncedQuery = useDebounce(query, debounceMs);

  useEffect(() => {
    const abortController = new AbortController();

    async function fetchResults() {
      setIsLoading(true);
      try {
        const response = await fetch(
          `${apiEndpoint}?q=${encodeURIComponent(debouncedQuery)}`,
          { signal: abortController.signal }
        );

        if (!response.ok) {
          throw new Error(`Search failed: ${response.status}`);
        }

        const data: SearchResult[] = await response.json();
        setResults(data);
        setIsOpen(data.length > 0);
        setActiveIndex(-1);
      } catch (error: any) {
        if (error.name !== "AbortError") {
          console.error("Search error:", error);
          setResults([]);
        }
      } finally {
        setIsLoading(false);
      }
    }

    fetchResults();

    return () => {
      // cleanup
    };
  }, [debouncedQuery, apiEndpoint]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setQuery(e.target.value);
    },
    []
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setActiveIndex((prev) =>
            prev < results.length - 1 ? prev + 1 : prev
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setActiveIndex((prev) => (prev > 0 ? prev - 1 : prev));
          break;
        case "Enter":
          e.preventDefault();
          if (activeIndex >= 0 && activeIndex < results.length) {
            handleSelect(results[activeIndex]);
          }
          break;
        case "Escape":
          setIsOpen(false);
          setActiveIndex(-1);
          break;
      }
    },
    [isOpen, results, activeIndex]
  );

  const handleSelect = useCallback(
    (result: SearchResult) => {
      setQuery(result.title);
      setIsOpen(false);
      setActiveIndex(-1);
      onSelect(result);
    },
    [onSelect]
  );

  return (
    <div className="search-autocomplete" style={{ position: "relative" }}>
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => results.length > 0 && setIsOpen(true)}
        placeholder={placeholder}
        role="combobox"
        aria-expanded={isOpen}
        aria-autocomplete="list"
        aria-activedescendant={
          activeIndex >= 0 ? `result-${results[activeIndex]?.id}` : undefined
        }
        className="search-input"
      />
      {isLoading && <span className="search-spinner" />}

      {isOpen && (
        <div
          ref={dropdownRef}
          role="listbox"
          className="search-dropdown"
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            maxHeight: 300,
            overflowY: "auto",
            backgroundColor: "white",
            border: "1px solid #ddd",
            borderRadius: 4,
            boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            zIndex: 1000,
          }}
        >
          {results.map((result, index) => (
            <div
              key={result.id}
              id={`result-${result.id}`}
              role="option"
              aria-selected={index === activeIndex}
              onClick={() => handleSelect(result)}
              onMouseEnter={() => setActiveIndex(index)}
              style={{
                padding: "8px 12px",
                cursor: "pointer",
                backgroundColor:
                  index === activeIndex ? "#f0f0f0" : "transparent",
              }}
            >
              <div
                className="result-title"
                dangerouslySetInnerHTML={{ __html: result.highlightedTitle }}
              />
              <div
                className="result-category"
                style={{ fontSize: 12, color: "#666" }}
              >
                {result.category}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
