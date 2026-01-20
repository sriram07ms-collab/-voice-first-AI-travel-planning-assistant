/**
 * Structured error logging system for frontend.
 * Logs errors in JSON format for automated error detection and fixing.
 */

interface ErrorLogEntry {
  timestamp: string;
  category: string;
  error_type: string;
  error_message: string;
  stack?: string;
  url?: string;
  user_agent?: string;
  auto_fixable: boolean;
  fix_suggestion?: string;
  context?: Record<string, any>;
  request_info?: Record<string, any>;
}

enum ErrorCategory {
  API_ERROR = 'api_error',
  NETWORK_ERROR = 'network_error',
  VALIDATION_ERROR = 'validation_error',
  RENDERING_ERROR = 'rendering_error',
  STATE_ERROR = 'state_error',
  PERMISSION_ERROR = 'permission_error',
  CONFIGURATION_ERROR = 'configuration_error',
  UNKNOWN_ERROR = 'unknown_error',
}

class ErrorLogger {
  private logFile: string = 'error_log.jsonl';
  private logs: ErrorLogEntry[] = [];
  private maxLogs: number = 100;

  constructor() {
    // Load existing logs from localStorage
    this.loadLogs();
  }

  private loadLogs(): void {
    try {
      if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
        const stored = localStorage.getItem('frontend_error_logs');
        if (stored) {
          this.logs = JSON.parse(stored).slice(-this.maxLogs);
        }
      }
    } catch (e) {
      console.warn('Failed to load error logs from localStorage', e);
    }
  }

  private saveLogs(): void {
    try {
      if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
        localStorage.setItem('frontend_error_logs', JSON.stringify(this.logs.slice(-this.maxLogs)));
      }
      
      // Also log to console for development (readable format)
      if (process.env.NODE_ENV === 'development') {
        const lastLog = this.logs[this.logs.length - 1];
        console.error(`Error logged: [${lastLog.category}] ${lastLog.error_message}`);
        if (lastLog.fix_suggestion) {
          console.info(`💡 Fix: ${lastLog.fix_suggestion}`);
        }
      }
    } catch (e) {
      console.warn('Failed to save error logs to localStorage', e);
    }
  }

  private detectErrorPattern(error: Error | string, context?: Record<string, any>): {
    category: ErrorCategory;
    auto_fixable: boolean;
    fix_suggestion?: string;
  } {
    const errorStr = typeof error === 'string' ? error : error.message.toLowerCase();
    const errorName = typeof error === 'string' ? 'Error' : error.name.toLowerCase();

    // Ignore harmless Next.js errors (404 for missing assets like favicon)
    if (errorStr.includes('next_not_found') || 
        (context && (context.filename && context.filename.includes('favicon')))) {
      return {
        category: ErrorCategory.UNKNOWN_ERROR,
        auto_fixable: true,
        fix_suggestion: 'Harmless Next.js 404 - can be ignored (likely missing favicon or asset)',
      };
    }

    // Pattern detection
    if (errorStr.includes('cors') || errorStr.includes('access-control')) {
      return {
        category: ErrorCategory.CONFIGURATION_ERROR,
        auto_fixable: true,
        fix_suggestion: 'Add frontend origin to backend CORS_ORIGINS',
      };
    }

    if (errorStr.includes('network') || errorStr.includes('fetch failed')) {
      return {
        category: ErrorCategory.NETWORK_ERROR,
        auto_fixable: false,
        fix_suggestion: 'Check network connection or backend availability',
      };
    }

    if (errorStr.includes('401') || errorStr.includes('unauthorized')) {
      return {
        category: ErrorCategory.PERMISSION_ERROR,
        auto_fixable: false,
        fix_suggestion: 'Check authentication token or login status',
      };
    }

    if (errorStr.includes('404') || errorStr.includes('not found')) {
      return {
        category: ErrorCategory.API_ERROR,
        auto_fixable: false,
        fix_suggestion: 'Verify API endpoint URL and route exists',
      };
    }

    if (errorStr.includes('500') || errorStr.includes('internal server error')) {
      return {
        category: ErrorCategory.API_ERROR,
        auto_fixable: false,
        fix_suggestion: 'Check backend logs for server error details',
      };
    }

    if (errorStr.includes('cannot read property') || errorStr.includes('undefined')) {
      return {
        category: ErrorCategory.STATE_ERROR,
        auto_fixable: true,
        fix_suggestion: 'Add null checks or default values',
      };
    }

    if (errorName.includes('typeerror') || errorName.includes('referenceerror')) {
      return {
        category: ErrorCategory.RENDERING_ERROR,
        auto_fixable: true,
        fix_suggestion: 'Fix variable reference or type issue',
      };
    }

    return {
      category: ErrorCategory.UNKNOWN_ERROR,
      auto_fixable: false,
      fix_suggestion: 'Manual investigation required',
    };
  }

  logError(
    error: Error | string,
    category?: ErrorCategory,
    context?: Record<string, any>,
    requestInfo?: Record<string, any>
  ): ErrorLogEntry {
    const pattern = category
      ? { category, auto_fixable: false }
      : this.detectErrorPattern(error, context);

    const errorEntry: ErrorLogEntry = {
      timestamp: new Date().toISOString(),
      category: pattern.category,
      error_type: typeof error === 'string' ? 'StringError' : error.name || 'Error',
      error_message: typeof error === 'string' ? error : error.message,
      stack: typeof error === 'string' ? undefined : error.stack,
      url: typeof window !== 'undefined' ? window.location.href : undefined,
      user_agent: typeof window !== 'undefined' ? navigator.userAgent : undefined,
      auto_fixable: pattern.auto_fixable,
      fix_suggestion: pattern.fix_suggestion,
      context: context || {},
      request_info: requestInfo || {},
    };

    this.logs.push(errorEntry);
    this.saveLogs();

    // Export logs for download/debugging
    this.exportLogsIfNeeded();

    return errorEntry;
  }

  private exportLogsIfNeeded(): void {
    // Export logs to console in development
    if (process.env.NODE_ENV === 'development' && this.logs.length > 0) {
      // Filter out harmless errors before displaying
      const meaningfulErrors = this.logs
        .filter(log => {
          const msg = log.error_message?.toLowerCase() || '';
          const type = log.error_type?.toLowerCase() || '';
          // Don't show Next.js 404 errors or favicon errors
          return !msg.includes('next_not_found') && 
                 !msg.includes('favicon') &&
                 !type.includes('next_not_found');
        })
        .slice(-5); // Last 5 meaningful errors
      
      if (meaningfulErrors.length > 0) {
        console.group('Recent Errors');
        meaningfulErrors.forEach((log) => {
          const msg = `[${log.category}] ${log.error_type}: ${log.error_message}`;
          // Only log the entry object if it has useful context
          if (log.context && Object.keys(log.context).length > 0) {
            console.error(msg, { context: log.context, request: log.request_info });
          } else {
            console.error(msg);
          }
          if (log.fix_suggestion && !log.fix_suggestion.includes('can be ignored')) {
            console.info(`💡 Fix suggestion: ${log.fix_suggestion}`);
          }
        });
        console.groupEnd();
      }
    }
  }

  getLogs(): ErrorLogEntry[] {
    return [...this.logs];
  }

  getLogsByCategory(category: ErrorCategory): ErrorLogEntry[] {
    return this.logs.filter((log) => log.category === category);
  }

  getAutoFixableErrors(): ErrorLogEntry[] {
    return this.logs.filter((log) => log.auto_fixable);
  }

  clearLogs(): void {
    this.logs = [];
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      localStorage.removeItem('frontend_error_logs');
    }
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  downloadLogs(): void {
    const data = this.exportLogs();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `error_logs_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

// Global error logger instance
export const errorLogger = new ErrorLogger();
export { ErrorCategory };
export type { ErrorLogEntry };

// Auto-log unhandled errors
if (typeof window !== 'undefined') {
  window.addEventListener('error', (event) => {
    // Filter out harmless errors (favicon 404s, Next.js internal 404s)
    const errorMessage = event.message?.toLowerCase() || '';
    const filename = event.filename?.toLowerCase() || '';
    
    // Skip logging for:
    // - Favicon requests
    // - Next.js internal 404 errors (NEXT_NOT_FOUND)
    // - Missing asset files that don't affect functionality
    if (filename.includes('favicon') || 
        errorMessage.includes('next_not_found') ||
        errorMessage.includes('not found') && filename.includes('_next')) {
      return; // Silently ignore these harmless errors
    }

    errorLogger.logError(event.error || event.message, undefined, {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    // Filter out Next.js 404 rejections
    const reasonStr = String(event.reason).toLowerCase();
    if (reasonStr.includes('next_not_found')) {
      return; // Silently ignore Next.js 404 rejections
    }

    errorLogger.logError(
      event.reason instanceof Error ? event.reason : new Error(String(event.reason)),
      ErrorCategory.API_ERROR,
      { promise_rejection: true }
    );
  });
}
