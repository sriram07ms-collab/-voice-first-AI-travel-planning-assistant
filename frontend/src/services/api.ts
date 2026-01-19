/**
 * API client for backend communication.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { errorLogger, ErrorCategory } from '../utils/errorLogger';
import type {
  ChatRequest,
  ChatResponse,
  PlanRequest,
  PlanResponse,
  EditRequest,
  EditResponse,
  ExplainRequest,
  ExplainResponse,
  GeneratePDFRequest,
  PDFResponse,
  ErrorResponse
} from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 120000, // 120 seconds for LLM requests (increased for complex queries)
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add any auth tokens here if needed
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error: AxiosError<ErrorResponse>) => {
        // Handle errors globally with error logging
        if (error.response) {
          // Server responded with error
          const errorData = error.response.data;
          const errorMessage = typeof errorData === 'string' ? errorData : (errorData?.message || errorData?.detail || 'API Error');
          const status = error.response.status;
          
          errorLogger.logError(
            new Error(errorMessage),
            ErrorCategory.API_ERROR,
            { 
              status: status,
              status_text: error.response.statusText,
              error_data: typeof errorData === 'object' ? errorData : { message: errorData }
            },
            { 
              url: error.config?.url, 
              method: error.config?.method,
              base_url: error.config?.baseURL
            }
          );
          
          // More helpful console logging
          console.error(`[API Error ${status}] ${error.config?.method?.toUpperCase()} ${error.config?.url}:`, errorMessage);
          if (typeof errorData === 'object' && errorData !== null) {
            console.error('Error details:', errorData);
          }
          
          return Promise.reject(errorData);
        } else if (error.request) {
          // Request made but no response - backend might be down
          const url = error.config?.url || 'unknown';
          const baseUrl = error.config?.baseURL || API_URL;
          const fullUrl = url.startsWith('http') ? url : `${baseUrl}${url}`;
          
          errorLogger.logError(
            new Error(`Backend not responding: ${fullUrl}`),
            ErrorCategory.NETWORK_ERROR,
            {
              error_code: error.code,
              timeout: error.code === 'ECONNABORTED',
              connection_refused: error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED'
            },
            { 
              url: url,
              full_url: fullUrl,
              method: error.config?.method,
              base_url: baseUrl
            }
          );
          
          // More helpful console logging
          if (error.code === 'ECONNABORTED') {
            console.error(`[Network Error] Request timeout: ${error.config?.method?.toUpperCase()} ${fullUrl}`);
          } else if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
            console.error(`[Network Error] Backend not accessible: ${baseUrl}`);
            console.error('  → Check if backend server is running on port 8000');
            console.error('  → Verify CORS configuration allows frontend origin');
          } else {
            console.error(`[Network Error] ${error.code || 'Unknown'}: ${fullUrl}`, error.message);
          }
          
          return Promise.reject({
            status: 'error',
            error_type: 'NETWORK_ERROR',
            message: `Cannot connect to backend at ${baseUrl}. Please check if the server is running.`,
            details: {
              base_url: baseUrl,
              error_code: error.code,
              suggestion: 'Make sure the backend server is started and accessible'
            }
          });
        } else {
          // Error setting up request
          errorLogger.logError(
            error,
            ErrorCategory.UNKNOWN_ERROR,
            {},
            { url: error.config?.url, method: error.config?.method }
          );
          console.error('Error:', error.message);
          return Promise.reject({
            status: 'error',
            error_type: 'UNKNOWN_ERROR',
            message: error.message,
          });
        }
      }
    );
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await this.client.post<ChatResponse>('/api/chat', request);
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async planTrip(request: PlanRequest): Promise<PlanResponse> {
    try {
      const response = await this.client.post<PlanResponse>('/api/plan', request);
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async editItinerary(request: EditRequest): Promise<EditResponse> {
    try {
      const response = await this.client.post<EditResponse>('/api/edit', request);
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async explainDecision(request: ExplainRequest): Promise<ExplainResponse> {
    try {
      const response = await this.client.post<ExplainResponse>('/api/explain', request);
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  private handleError(error: any): ErrorResponse {
    // Handle Axios error response
    if (error.response) {
      const data = error.response.data;
      // FastAPI returns {detail: "message"} for HTTPException
      if (data.detail && !data.status) {
        return {
          status: 'error',
          error_type: error.response.status === 501 ? 'NOT_IMPLEMENTED' : 'HTTP_ERROR',
          message: data.detail,
        };
      }
      // Already formatted ErrorResponse
      return data as ErrorResponse;
    } else if (error.request) {
      return {
        status: 'error',
        error_type: 'NETWORK_ERROR',
        message: 'Network error. Please check your connection.',
      };
    } else {
      return {
        status: 'error',
        error_type: 'UNKNOWN_ERROR',
        message: error.message || 'An unexpected error occurred',
      };
    }
  }

  async generatePDF(request: GeneratePDFRequest): Promise<PDFResponse> {
    const response = await this.client.post<PDFResponse>('/api/generate-pdf', request);
    return response.data;
  }

  async healthCheck(): Promise<any> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
