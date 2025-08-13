import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class Api {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = environment.apiBaseUrl || '';
  private readonly apiBasePath = '';

  get<T>(path: string, options: { params?: Record<string, string> } = {}): Observable<T> {
    const url = this.composeUrl(path);
    return this.http.get<T>(url, { params: options.params, withCredentials: true });
  }

  post<T>(path: string, body: unknown, headers: Record<string, string> = {}): Observable<T> {
    const url = this.composeUrl(path);
    const httpHeaders = new HttpHeaders(headers);
    return this.http.post<T>(url, body, { headers: httpHeaders, withCredentials: true });
  }

  private composeUrl(path: string): string {
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${this.apiBaseUrl}${this.apiBasePath}${normalizedPath}`;
  }
}
