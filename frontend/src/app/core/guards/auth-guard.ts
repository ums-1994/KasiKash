import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { Auth } from '../services/auth';
import { map } from 'rxjs/operators';

export const authGuard: CanActivateFn = (route, state) => {
  const auth = inject(Auth);
  const router = inject(Router);
  return auth.isAuthenticated().pipe(
    map(isAuthed => {
      if (isAuthed) {
        return true;
      }
      router.navigate(['/login'], { queryParams: { redirect: state.url } });
      return false;
    })
  );
};
