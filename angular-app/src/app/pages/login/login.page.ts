import { AfterViewInit, Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div id="particles-js"></div>
    <div class="globe-container" id="globe"></div>
    <div class="content-wrapper relative z-10">
      <nav class="fixed w-full z-50 bg-black bg-opacity-50 backdrop-blur-md p-4 transition-all duration-300">
        <div class="container mx-auto flex justify-between items-center">
          <a routerLink="/welcome" class="flex items-center space-x-3">
            <span class="text-2xl font-bold text-gradient glow">KasiKash</span>
          </a>
          <ul class="hidden md:flex space-x-8">
            <li><a routerLink="/" class="nav-link text-white hover:text-cyan-300 font-medium">Home</a></li>
            <li><a routerLink="/login" class="nav-link text-white hover:text-cyan-300 font-medium">Login</a></li>
          </ul>
        </div>
      </nav>

      <main class="min-h-screen flex items-center justify-center pt-20 pb-12 px-4">
        <div class="login-card max-w-md w-full p-8 rounded-2xl shadow-xl transform transition-all duration-500">
          <h2 class="text-3xl font-bold mb-8 text-center text-gradient">Welcome Back</h2>
          <form (submit)="onSubmit($event)" class="space-y-6">
            <div class="relative">
              <input type="email" class="input-field w-full py-3 px-5 pr-12 rounded-full" [(ngModel)]="email" name="email" placeholder="Email" />
              <i class="fas fa-envelope input-icon absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
            </div>
            <div class="relative">
              <input type="password" class="input-field w-full py-3 px-5 pr-12 rounded-full" [(ngModel)]="password" name="password" placeholder="Password" />
              <i class="fas fa-lock input-icon absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
            </div>
            <button type="submit" class="btn-primary">Login</button>
            <div class="text-center text-gray-300">
              Don't have an account?
              <a routerLink="/signup" class="text-ocean-2 hover:text-ocean-3 font-medium">Register</a>
            </div>
          </form>
        </div>
      </main>

      <footer class="bg-black text-white py-12">
        <div class="container mx-auto px-4">
          <div class="border-t border-gray-800 pt-8 text-center text-gray-400">
            <p>&copy; 2025 KasiKash. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  `,
  styles: [`
    :host { display:block; }
    .text-gradient { background: linear-gradient(90deg, #60efff, #00ff87); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .glow { text-shadow: 0 0 10px rgba(96,239,255,0.7); }
    .login-card { backdrop-filter: blur(20px); background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 1.5rem; }
    .input-field { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #fff; }
    .input-field::placeholder { color: rgba(255,255,255,0.5); }
    .btn-primary { width: 100%; padding: 0.75rem 1rem; background: linear-gradient(135deg, #60efff, #00ff87); color: #000; font-weight: 600; border-radius: 0.5rem; }
    .globe-container { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; opacity: 0.25; }
  `]
})
export class LoginPage implements AfterViewInit {
  email = '';
  password = '';

  constructor(private api: ApiService, private router: Router) {}

  onSubmit(e: Event) {
    e.preventDefault();
    // Mock login: set current user and redirect
    this.api.setCurrentUser({ name: 'John Doe', email: this.email || 'john.doe@example.com', avatar: 'assets/default-avatar.png' });
    this.router.navigate(['/dashboard']);
  }

  ngAfterViewInit(): void {
    const container = document.getElementById('globe');
    const THREE_ANY: any = (window as any).THREE;
    if (container && THREE_ANY) {
      const scene = new THREE_ANY.Scene();
      const camera = new THREE_ANY.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
      const renderer = new THREE_ANY.WebGLRenderer({ alpha: true, antialias: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      container.appendChild(renderer.domElement);
      const geometry = new THREE_ANY.SphereGeometry(5, 32, 32);
      const material = new THREE_ANY.MeshBasicMaterial({ color: 0x45caff, wireframe: true, transparent: true, opacity: 0.25 });
      const sphere = new THREE_ANY.Mesh(geometry, material);
      scene.add(sphere);
      camera.position.z = 8;
      const animate = () => { requestAnimationFrame(animate); sphere.rotation.x += 0.001; sphere.rotation.y += 0.002; renderer.render(scene, camera); };
      window.addEventListener('resize', () => { camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); });
      animate();
    }
    const gsap: any = (window as any).gsap;
    if (gsap) {
      gsap.from('.login-card', { y: 20, opacity: 0, duration: 1, ease: 'back.out(1.7)' });
    }
  }
}

