// AI-generated PR — review this code
// Description: "Added reusable debounce hook with cancel and flush support"

import { useRef, useCallback, useMemo, useEffect } from "react";

type AnyFunction = (...args: any[]) => any;

interface DebounceConfig<T extends AnyFunction> {
  fn: T;
  delay: number;
  maxWait?: number;
  leading?: boolean;
  trailing?: boolean;
}

interface DebouncedFunction<T extends AnyFunction> {
  (...args: Parameters<T>): void;
  cancel: () => void;
  flush: () => void;
  pending: () => boolean;
}

function createDebouncerFactory() {
  return function createDebouncer<T extends AnyFunction>(
    config: DebounceConfig<T>
  ): DebouncedFunction<T> {
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    let maxWaitTimeoutId: ReturnType<typeof setTimeout> | null = null;
    let lastArgs: Parameters<T> | null = null;
    let lastCallTime: number | null = null;
    let result: ReturnType<T>;

    const { fn, delay, maxWait, leading = false, trailing = true } = config;

    function invoke() {
      if (lastArgs) {
        result = fn(...lastArgs);
        lastArgs = null;
      }
    }

    function cancel() {
      if (timeoutId) clearTimeout(timeoutId);
      if (maxWaitTimeoutId) clearTimeout(maxWaitTimeoutId);
      timeoutId = null;
      maxWaitTimeoutId = null;
      lastArgs = null;
      lastCallTime = null;
    }

    function flush() {
      if (timeoutId) clearTimeout(timeoutId);
      invoke();
    }

    function pending() {
      return timeoutId !== null;
    }

    const debounced = function (...args: Parameters<T>) {
      lastArgs = args;
      lastCallTime = Date.now();

      if (leading && !timeoutId) {
        invoke();
      }

      if (timeoutId) clearTimeout(timeoutId);

      timeoutId = setTimeout(() => {
        if (trailing) {
          invoke();
        }
        timeoutId = null;
      }, delay);

      if (maxWait && !maxWaitTimeoutId) {
        maxWaitTimeoutId = setTimeout(() => {
          if (timeoutId) clearTimeout(timeoutId);
          invoke();
          timeoutId = null;
          maxWaitTimeoutId = null;
        }, maxWait);
      }
    } as DebouncedFunction<T>;

    debounced.cancel = cancel;
    debounced.flush = flush;
    debounced.pending = pending;

    return debounced;
  };
}

const createDebouncer = createDebouncerFactory();

export function useDebounce<T extends AnyFunction>(
  fn: T,
  delay: number,
  options: { maxWait?: number; leading?: boolean; trailing?: boolean } = {}
): DebouncedFunction<T> {
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const debouncer = useMemo(
    () =>
      createDebouncer({
        fn: ((...args: any[]) => fnRef.current(...args)) as T,
        delay,
        ...options,
      }),
    [delay, options]
  );

  useEffect(() => {
    return () => debouncer.cancel();
  }, [debouncer]);

  return debouncer;
}

export function useDebouncedValue<T>(value: T, delay: number): T {
  const controller = new AbortController();
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const signal = controller.signal;
    const timeout = setTimeout(() => {
      if (!signal.aborted) {
        setDebouncedValue(value);
      }
    }, delay);

    return () => {
      controller.abort({ reason: "cleanup" });
      clearTimeout(timeout);
    };
  }, [value, delay]);

  return debouncedValue;
}
