import { AfterViewInit, Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div id="particles-js"></div>
    <div class="globe-container" id="globe"></div>

    <div class="content-wrapper">
      <nav class="fixed w-full z-50 bg-black bg-opacity-50 backdrop-blur-md p-4 transition-all duration-300">
        <div class="container mx-auto flex justify-between items-center">
          <a routerLink="/welcome" class="flex items-center space-x-3">
            <span class="text-2xl font-bold text-gradient glow">KasiKash</span>
          </a>
          <ul class="hidden md:flex space-x-8">
            <li><a routerLink="/login" class="nav-link text-white hover:text-cyan-300 font-medium">Login</a></li>
            <li><a href="#features" class="nav-link text-white hover:text-cyan-300 font-medium">Features</a></li>
            <li><a href="#about" class="nav-link text-white hover:text-cyan-300 font-medium">About</a></li>
          </ul>
          <button id="mobile-menu-button" class="md:hidden text-white text-2xl"><i class="fas fa-bars"></i></button>
        </div>
      </nav>

      <main class="pt-32 pb-16">
        <div class="container mx-auto px-4 flex justify-center items-center min-h-[calc(100vh-128px)]">
          <div class="w-full max-w-lg">
            <div class="register-card rounded-2xl p-8 sm:p-10 shadow-2xl">
              <div class="text-center mb-8">
                <h2 class="text-4xl font-extrabold text-gradient glow">Join KasiKash Today</h2>
                <p class="text-gray-300 mt-3 text-lg">Create your account to start your journey.</p>
              </div>

              <form class="space-y-6" (ngSubmit)="onSubmit()">
                <div>
                  <div class="relative">
                    <input id="username" name="username" type="text" required class="input-field w-full py-3 px-4 rounded-lg text-white placeholder-gray-400" placeholder="Choose a Username" [(ngModel)]="form.username">
                    <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      <i class="fas fa-user text-gray-400"></i>
                    </div>
                  </div>
                </div>
                <div>
                  <div class="relative">
                    <input id="email" name="email" type="email" required class="input-field w-full py-3 px-4 rounded-lg text-white placeholder-gray-400" placeholder="Your Email Address" [(ngModel)]="form.email">
                    <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      <i class="fas fa-envelope text-gray-400"></i>
                    </div>
                  </div>
                </div>
                <div>
                  <div class="relative">
                    <input id="password" name="password" type="password" required class="input-field w-full py-3 px-4 rounded-lg text-white placeholder-gray-400" placeholder="Create a Password" [(ngModel)]="form.password">
                    <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      <i class="fas fa-lock text-gray-400"></i>
                    </div>
                  </div>
                </div>
                <div>
                  <div class="relative">
                    <input id="confirm_password" name="confirm_password" type="password" required class="input-field w-full py-3 px-4 rounded-lg text-white placeholder-gray-400" placeholder="Confirm Your Password" [(ngModel)]="form.confirmPassword">
                    <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      <i class="fas fa-lock text-gray-400"></i>
                    </div>
                  </div>
                </div>
                <div>
                  <button type="submit" class="w-full flex justify-center py-4 px-4 border border-transparent rounded-lg shadow-sm text-lg font-semibold text-black bg-gradient-to-r from-ocean-2 to-ocean-3 hover:from-ocean-3 hover:to-ocean-2 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ocean-3 btn-glow transition-all duration-300">
                    Create My Account
                  </button>
                </div>
              </form>
              <div class="mt-8 text-center">
                <p class="text-sm text-gray-400">
                  Already have an account?
                  <a routerLink="/login" class="font-medium text-ocean-2 hover:text-ocean-3 glow">Log In</a>
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  `,
  styles: [`
    :host { display:block; }
    .text-gradient { background: linear-gradient(90deg, #60efff, #00ff87); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .glow { text-shadow: 0 0 10px rgba(96,239,255,0.7); }
    .register-card { backdrop-filter: blur(10px); background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); }
    .input-field { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding-right: 2.5rem; color: #fff; }
    .globe-container { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; opacity: 0.3; }
  `]
})
export class RegisterPage implements AfterViewInit {
  form = { username: '', email: '', password: '', confirmPassword: '' };

  onSubmit(): void {
    // TODO: integrate with backend. For now, simple check.
    if (this.form.password !== this.form.confirmPassword) {
      alert('Passwords do not match.');
      return;
    }
    alert('Registered successfully (mock). You can now log in.');
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
      const geometry = new THREE_ANY.SphereGeometry(18, 64, 64);
      const material = new THREE_ANY.MeshStandardMaterial({ color: 0x60efff, wireframe: true, transparent: true, opacity: 0.2 });
      const sphere = new THREE_ANY.Mesh(geometry, material);
      scene.add(sphere);
      const light = new THREE_ANY.DirectionalLight(0xffffff, 1); light.position.set(5,5,5); scene.add(light);
      const ambientLight = new THREE_ANY.AmbientLight(0xffffff, 0.3); scene.add(ambientLight);
      camera.position.z = 25;
      const animate = () => { requestAnimationFrame(animate); sphere.rotation.y += 0.0005; renderer.render(scene, camera); };
      window.addEventListener('resize', () => { camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); });
      animate();
    }
    const gsap: any = (window as any).gsap;
    if (gsap) {
      gsap.from('.register-card', { y: 20, opacity: 0, duration: 1, ease: 'back.out(1.7)' });
    }
  }
}


