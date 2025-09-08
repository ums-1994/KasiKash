import { AfterViewInit, Component } from '@angular/core';
import { RouterModule } from '@angular/router';

declare const THREE: any;
declare const gsap: any;
declare const ScrollTrigger: any;

@Component({
  selector: 'app-welcome',
  standalone: true,
  template: `
    <div class="content-wrapper">
      <nav class="fixed w-full z-50 bg-white bg-opacity-95 backdrop-blur-md p-4 transition-all duration-300 border-b border-gray-200">
        <div class="container mx-auto flex justify-between items-center">
          <a routerLink="/welcome" class="flex items-center space-x-3">
            <span class="text-2xl font-bold text-gradient glow">KasiKash</span>
          </a>
          <ul class="hidden md:flex space-x-8">
            <li><a routerLink="/login" class="nav-link font-medium">Login</a></li>
            <li><a routerLink="/pricing" class="nav-link font-medium">Pricing</a></li>
            <li><a href="#features" class="nav-link font-medium">Features</a></li>
            <li class="dropdown">
              <a routerLink="/contact" class="nav-link font-medium">Contact</a>
              <div class="dropdown-content">
                <div class="contact-info text-gray-700">
                  <p class="mb-3"><i class="fas fa-envelope text-2E8B57"></i> Email: support@kasikash.co.za</p>
                  <p class="mb-3"><i class="fas fa-phone text-2E8B57"></i> Phone: +27 11 123 4567</p>
                  <p><i class="fas fa-map-marker-alt text-2E8B57"></i> Address: Johannesburg, South Africa</p>
                </div>
              </div>
            </li>
            <li><a href="#about" class="nav-link font-medium">About</a></li>
          </ul>
          <button class="md:hidden text-gray-700">
            <i class="fas fa-bars text-2xl"></i>
          </button>
        </div>
      </nav>

      <section class="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
        <!-- 3D Globe Background -->
        <div class="globe-container" id="globe"></div>
        <div class="container mx-auto px-4 py-20 text-center relative z-10">
          <!-- Text background overlay for better visibility -->
          <div class="text-background-overlay"></div>
          <h1 class="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            <span class="text-gradient-bright-light">Digital Stokvels</span><br />
            <span class="text-gradient-secondary-light">for Modern Communities</span>
          </h1>
          <p class="text-xl md:text-2xl text-gradient-text-light mb-12 max-w-3xl mx-auto leading-relaxed font-semibold">
            Transform your stokvel with secure digital management, smart investments, and community growth tools.
          </p>
          <div class="flex flex-col sm:flex-row justify-center gap-4">
            <a routerLink="/register" class="btn-bright bg-white text-gray-900 font-bold py-4 px-8 rounded-full text-lg transition duration-300 transform hover:scale-105 shadow-2xl hover:shadow-3xl border-2 border-gray-200">
              Start Free Trial <i class="fas fa-arrow-right ml-2"></i>
            </a>
          </div>
        </div>
        <div class="wave-shape">
          <svg data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120" preserveAspectRatio="none">
            <path d="M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.36-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,209.4,13.08,36.15-6,69.85-17.84,104.45-29.34C989.49,25,1113-14.29,1200,52.47V0Z" opacity=".25" class="shape-fill"></path>
            <path d="M0,0V15.81C13,36.92,27.64,56.86,47.69,72.05,99.41,111.27,165,111,224.58,91.58c31.15-10.15,60.09-26.07,89.67-39.8,40.92-19,84.73-46,130.83-49.67,36.26-2.85,70.9,9.42,98.6,31.56,31.77,25.39,62.32,62,103.63,73,40.44,10.79,81.35-6.69,119.13-24.28s75.16-39,116.92-43.05c59.73-5.85,113.28,22.88,168.9,38.84,30.2,8.66,59,6.17,87.09-7.5,22.43-10.89,48-26.93,60.65-49.24V0Z" opacity=".5" class="shape-fill"></path>
            <path d="M0,0V5.63C149.93,59,314.09,71.32,475.83,42.57c43-7.64,84.23-20.12,127.61-26.46,59-8.63,112.48,12.24,165.56,35.4C827.93,77.22,886,95.24,951.2,90c86.53-7,172.46-45.71,248.8-84.81V0Z" class="shape-fill"></path>
          </svg>
        </div>
      </section>

      <section id="features" class="py-20 bg-gray-50 relative overflow-hidden">
        <div class="container mx-auto px-4">
          <div class="text-center mb-16">
            <h2 class="text-4xl font-bold mb-4 text-gradient">Why Choose KasiKash?</h2>
            <p class="text-xl text-gray-700 max-w-3xl mx-auto font-medium">
              Built specifically for South African communities with features that matter most to stokvel success.
            </p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div class="card-hover bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
              <div class="feature-icon text-5xl mb-6 text-center" style="color: #2E8B57;">
                <i class="fas fa-shield-alt"></i>
              </div>
              <h3 class="text-2xl font-bold mb-4 text-gray-900">SARB Regulated</h3>
              <p class="text-gray-700 font-medium">
                Licensed and regulated financial services provider with full compliance to South African Reserve Bank standards.
              </p>
            </div>

            <div class="card-hover bg-white p-8 rounded-2xl shadow-lg border border-gray-200 transform transition-all duration-500 hover:scale-105">
              <div class="feature-icon text-5xl mb-6 text-center" style="color: #009879;">
                <i class="fas fa-lock"></i>
              </div>
              <h3 class="text-2xl font-bold mb-4 text-gray-900">Bank-Level Security</h3>
              <p class="text-gray-700 font-medium">
                256-bit encryption and secure infrastructure that meets global banking security standards.
              </p>
            </div>

            <div class="card-hover bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
              <div class="feature-icon text-5xl mb-6 text-center" style="color: #F5A623;">
                <i class="fas fa-users"></i>
              </div>
              <h3 class="text-2xl font-bold mb-4 text-gray-900">Community Focused</h3>
              <p class="text-gray-700 font-medium">
                Built by and for South African communities with features tailored to local needs and traditions.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section class="py-20 bg-white relative overflow-hidden">
        <div class="container mx-auto px-4">
          <div class="text-center mb-16">
            <h2 class="text-4xl font-bold mb-4 text-gradient">Our Features</h2>
            <p class="text-xl text-gray-700 max-w-3xl mx-auto font-medium">
              Everything you need to run a successful digital stokvel
            </p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div class="feature-card bg-gray-50 rounded-2xl p-8 border border-gray-200 hover:border-2E8B57 transition-all duration-300">
              <div class="feature-icon text-5xl mb-6 text-center" style="color: #2E8B57;">
                <i class="fas fa-wallet"></i>
              </div>
              <h3 class="text-2xl font-bold mb-4 text-gray-900">Smart Savings</h3>
              <p class="text-gray-700 font-medium">Automated contributions, compound interest, and goal tracking to maximize your stokvel's growth potential.</p>
            </div>
            <div class="feature-card bg-gray-50 rounded-2xl p-8 border border-gray-200 hover:border-009879 transition-all duration-300">
              <div class="feature-icon text-5xl mb-6 text-center" style="color: #009879;">
                <i class="fas fa-users"></i>
              </div>
              <h3 class="text-2xl font-bold mb-4 text-gray-900">Community Management</h3>
              <p class="text-gray-700 font-medium">Easy member onboarding, contribution tracking, and transparent financial reporting for all members.</p>
            </div>
            <div class="feature-card bg-gray-50 rounded-2xl p-8 border border-gray-200 hover:border-F5A623 transition-all duration-300">
              <div class="feature-icon text-5xl mb-6 text-center" style="color: #F5A623;">
                <i class="fas fa-lock"></i>
              </div>
              <h3 class="text-2xl font-bold mb-4 text-gray-900">Bank-Level Security</h3>
              <p class="text-gray-700 font-medium">Your money is protected with enterprise-grade security, encryption, and regulatory compliance.</p>
            </div>
            <div class="feature-card bg-gray-50 rounded-2xl p-8 border border-gray-200 hover:border-2E8B57 transition-all duration-300">
              <div class="feature-icon text-5xl mb-6 text-center" style="color: #2E8B57;">
                <i class="fas fa-trophy"></i>
              </div>
              <h3 class="text-2xl font-bold mb-4 text-gray-900">Community Success</h3>
              <p class="text-gray-700 font-medium">Real people achieving their financial dreams through our platform with proven results.</p>
            </div>
            <div class="feature-card bg-gray-50 rounded-2xl p-8 border border-gray-200 hover:border-009879 transition-all duration-300">
              <div class="feature-icon text-5xl mb-6 text-center" style="color: #009879;">
                <i class="fas fa-mobile-alt"></i>
              </div>
              <h3 class="text-2xl font-bold mb-4 text-gray-900">Easy-to-Use Platform</h3>
              <p class="text-gray-700 font-medium">Intuitive design that makes managing your stokvel simple and effective for all members.</p>
            </div>
            <div class="feature-card bg-gray-50 rounded-2xl p-8 border border-gray-200 hover:border-F5A623 transition-all duration-300">
              <div class="feature-icon text-5xl mb-6 text-center" style="color: #F5A623;">
                <i class="fas fa-store"></i>
              </div>
              <h3 class="text-2xl font-bold mb-4 text-gray-900">Events & Marketplace</h3>
              <p class="text-gray-700 font-medium">Access to exclusive events and a marketplace for your stokvel's needs with special discounts.</p>
            </div>
          </div>
        </div>
      </section>

      <section class="py-20 bg-gray-50 relative overflow-hidden">
        <div class="container mx-auto px-4">
          <div class="text-center mb-16">
            <h2 class="text-4xl font-bold mb-4 text-gradient">What Our Community Says</h2>
            <p class="text-xl text-gray-700 max-w-3xl mx-auto font-medium">Hear from stokvels that are already building wealth with KasiKash</p>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div class="card-hover bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
              <div class="flex items-center mb-6">
                <div class="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold text-white" style="background: #2E8B57;">T</div>
                <div class="ml-4">
                  <h4 class="text-xl font-bold text-gray-800">Thandi M.</h4>
                  <p class="text-gray-600">Johannesburg Stokvel</p>
                </div>
              </div>
              <p class="text-gray-600 italic">"KasiKash has transformed how our stokvel operates. We've grown our savings by 40% in just one year with their smart tools."</p>
              <div class="mt-4" style="color: #F5A623;">
                <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i>
              </div>
            </div>
            <div class="card-hover bg-white p-8 rounded-2xl shadow-lg border border-gray-200 transform transition-all duration-500 hover:scale-105">
              <div class="flex items-center mb-6">
                <div class="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold text-white" style="background: #009879;">S</div>
                <div class="ml-4">
                  <h4 class="text-xl font-bold text-gray-800">Sipho K.</h4>
                  <p class="text-gray-600">Cape Town Investment Club</p>
                </div>
              </div>
              <p class="text-gray-600 italic">"The security features gave us peace of mind, and the interest rates are better than any bank. Our members love the transparency."</p>
              <div class="mt-4" style="color: #F5A623;">
                <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i>
              </div>
            </div>
            <div class="card-hover bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
              <div class="flex items-center mb-6">
                <div class="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold text-white" style="background: #F5A623;">N</div>
                <div class="ml-4">
                  <h4 class="text-xl font-bold text-gray-800">Nomvula P.</h4>
                  <p class="text-gray-600">Durban Savings Group</p>
                </div>
              </div>
              <p class="text-gray-600 italic">"From burial society to property investors - KasiKash helped us level up our stokvel game. The platinum coaching is worth every cent!"</p>
              <div class="mt-4" style="color: #F5A623;">
                <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star-half-alt"></i>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="py-20 rainbow-gradient relative overflow-hidden">
        <div class="container mx-auto px-4 text-center">
          <h2 class="text-4xl md:text-5xl font-bold mb-6 text-white">Ready to Transform Your Stokvel?</h2>
          <p class="text-xl text-white mb-8 max-w-3xl mx-auto">Join thousands of South Africans building wealth together through trusted community savings.</p>
          <div class="flex flex-col sm:flex-row justify-center gap-4">
            <a routerLink="/register" class="bg-white text-gray-800 font-bold py-4 px-8 rounded-full text-lg transition duration-300 transform hover:scale-105 hover:bg-opacity-90">Start Your Free Trial</a>
          </div>
        </div>
      </section>

      <footer class="bg-gray-800 text-white py-12">
        <div class="container mx-auto px-4">
          <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h4 class="text-2xl font-bold mb-4 text-gradient glow">KasiKash</h4>
              <p class="text-gray-300 mb-4">Your digital stokvel platform for community wealth building.</p>
              <div class="flex space-x-4">
                <a href="#" class="text-gray-300 hover:text-2E8B57 transition duration-300"><i class="fab fa-facebook-f"></i></a>
                <a href="#" class="text-gray-300 hover:text-009879 transition duration-300"><i class="fab fa-twitter"></i></a>
                <a href="#" class="text-gray-300 hover:text-F5A623 transition duration-300"><i class="fab fa-instagram"></i></a>
                <a href="#" class="text-gray-300 hover:text-2E8B57 transition duration-300"><i class="fab fa-linkedin-in"></i></a>
              </div>
            </div>
            <div>
              <h4 class="text-xl font-bold mb-4 text-white">Quick Links</h4>
              <ul class="space-y-2">
                <li><a routerLink="/get_started" class="text-gray-300 hover:text-white">Get Started</a></li>
                <li><a href="#features" class="text-gray-300 hover:text-white">Features</a></li>
                <li><a routerLink="/contact" class="text-gray-300 hover:text-white">Contact</a></li>
                <li><a href="#about" class="text-gray-300 hover:text-white">About</a></li>
              </ul>
            </div>
            <div>
              <h4 class="text-xl font-bold mb-4 text-white">Legal</h4>
              <ul class="space-y-2">
                <li><a href="#" class="text-gray-300 hover:text-white">Terms of Service</a></li>
                <li><a href="#" class="text-gray-300 hover:text-white">Privacy Policy</a></li>
                <li><a href="#" class="text-gray-300 hover:text-white">Licenses</a></li>
              </ul>
            </div>
            <div>
              <h4 class="text-xl font-bold mb-4 text-white">Contact Us</h4>
              <ul class="space-y-2">
                <li class="text-gray-300">Email: support@kasikash.co.za</li>
                <li class="text-gray-300">Phone: +27 11 123 4567</li>
                <li class="text-gray-300">Address: Johannesburg, South Africa</li>
              </ul>
            </div>
          </div>
          <div class="border-t border-gray-700 mt-8 pt-8 text-center text-gray-300">
            <p>&copy; 2025 KasiKash. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  `,
  styles: [`
    :host { display: block; }
    body { font-family: 'Inter', sans-serif; background: #FFFFFF; color: #1a1a1a; overflow-x: hidden; }
    h1, h2, h3, h4, h5, h6 { font-family: 'Montserrat', sans-serif; color: #1a1a1a; font-weight: 700; }
    .rainbow-gradient { background: linear-gradient(135deg, #2E8B57 0%, #009879 25%, #F5A623 50%, #2E8B57 75%, #009879 100%); }
    .card-hover { transition: all 0.3s ease; transform-style: preserve-3d; }
    .card-hover:hover { transform: translateY(-10px) rotateX(5deg) rotateY(5deg); box-shadow: 0 20px 40px rgba(46,139,87,0.2); }
    .text-gradient { background: linear-gradient(90deg, #2E8B57, #009879); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
    .text-gradient-bright { 
      background: linear-gradient(135deg, #2E8B57 0%, #009879 25%, #F5A623 50%, #2E8B57 75%, #009879 100%); 
      -webkit-background-clip: text; 
      background-clip: text; 
      -webkit-text-fill-color: transparent; 
      text-shadow: 0 0 30px rgba(46,139,87,0.3);
    }
    .text-gradient-bright-light { 
      background: linear-gradient(135deg, #4CAF50 0%, #00BCD4 25%, #FFC107 50%, #4CAF50 75%, #00BCD4 100%); 
      -webkit-background-clip: text; 
      background-clip: text; 
      -webkit-text-fill-color: transparent; 
      text-shadow: 0 0 40px rgba(76,175,80,0.5), 0 0 20px rgba(0,188,212,0.4);
      filter: brightness(1.3) contrast(1.1);
    }
    .text-gradient-secondary { 
      background: linear-gradient(135deg, #009879 0%, #F5A623 50%, #2E8B57 100%); 
      -webkit-background-clip: text; 
      background-clip: text; 
      -webkit-text-fill-color: transparent; 
      text-shadow: 0 0 20px rgba(0,152,121,0.3);
    }
    .text-gradient-secondary-light { 
      background: linear-gradient(135deg, #00BCD4 0%, #FFC107 50%, #4CAF50 100%); 
      -webkit-background-clip: text; 
      background-clip: text; 
      -webkit-text-fill-color: transparent; 
      text-shadow: 0 0 35px rgba(0,188,212,0.6), 0 0 15px rgba(255,193,7,0.5);
      filter: brightness(1.4) contrast(1.2);
    }
    .text-gradient-text { 
      background: linear-gradient(135deg, #2E8B57 0%, #009879 100%); 
      -webkit-background-clip: text; 
      background-clip: text; 
      -webkit-text-fill-color: transparent; 
      text-shadow: 0 0 15px rgba(46,139,87,0.2);
    }
    .text-gradient-text-light { 
      background: linear-gradient(135deg, #4CAF50 0%, #00BCD4 100%); 
      -webkit-background-clip: text; 
      background-clip: text; 
      -webkit-text-fill-color: transparent; 
      text-shadow: 0 0 25px rgba(76,175,80,0.4), 0 0 10px rgba(0,188,212,0.3);
      filter: brightness(1.3) contrast(1.1);
    }
    .glow { text-shadow: 0 0 10px rgba(46,139,87,0.5); }
    .btn-glow { 
      box-shadow: 0 4px 15px rgba(46,139,87,0.3), 0 0 20px rgba(0,152,121,0.2); 
      transition: all 0.3s ease; 
      border: 2px solid rgba(255,255,255,0.1);
    }
    .btn-glow:hover { 
      box-shadow: 0 8px 25px rgba(46,139,87,0.5), 0 0 30px rgba(0,152,121,0.4); 
      transform: translateY(-3px);
      border-color: rgba(255,255,255,0.3);
    }
    .btn-bright { 
      box-shadow: 0 8px 25px rgba(0,0,0,0.15), 0 0 40px rgba(255,255,255,0.8); 
      transition: all 0.3s ease; 
      border: 2px solid rgba(0,0,0,0.1);
      background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    }
    .btn-bright:hover { 
      box-shadow: 0 12px 35px rgba(0,0,0,0.2), 0 0 50px rgba(255,255,255,1); 
      transform: translateY(-3px) scale(1.02);
      border-color: rgba(0,0,0,0.2);
      background: linear-gradient(135deg, #ffffff 0%, #f1f3f4 100%);
    }
    .nav-link { position: relative; color: #1a1a1a; font-weight: 500; }
    .nav-link::after { content: ''; position: absolute; width: 0; height: 2px; bottom: -5px; left: 0; background: linear-gradient(90deg, #2E8B57, #009879); transition: width 0.3s ease; }
    .nav-link:hover::after { width: 100%; }
    .nav-link:hover { color: #2E8B57; }
    .feature-icon { transition: all 0.5s ease; transform-style: preserve-3d; }
    .feature-card:hover .feature-icon { transform: rotateY(180deg) scale(1.2); }
    #globe.globe-container { 
      position: absolute; 
      top: 0; 
      left: 0; 
      width: 100%; 
      height: 100%; 
      z-index: 0; 
      opacity: 0.6; 
      pointer-events: none;
      background: radial-gradient(circle at center, rgba(46,139,87,0.05) 0%, rgba(0,152,121,0.03) 50%, transparent 70%);
    }
    
    .globe-container::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      width: 200px;
      height: 200px;
      background: radial-gradient(circle, rgba(46,139,87,0.1) 0%, transparent 70%);
      border-radius: 50%;
      transform: translate(-50%, -50%);
      animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
      0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
      50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.8; }
    }
    .content-wrapper { position: relative; z-index: 1; }
    
    .text-background-overlay {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 120%;
      height: 80%;
      background: radial-gradient(ellipse at center, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 50%, transparent 70%);
      border-radius: 50%;
      z-index: -1;
      pointer-events: none;
    }
    .section { position: relative; overflow: hidden; }
    .wave-shape { position: absolute; bottom: 0; left: 0; width: 100%; overflow: hidden; line-height: 0; }
    .wave-shape svg { position: relative; display: block; width: calc(100% + 1.3px); height: 150px; }
    .wave-shape .shape-fill { fill: #FFFFFF; }
    .dropdown { position: relative; display: inline-block; }
    .dropdown-content { display: none; position: absolute; right: 0; background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); min-width: 300px; border-radius: 0.5rem; padding: 1rem; z-index: 1000; border: 1px solid rgba(46,139,87,0.2); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
    .dropdown:hover .dropdown-content { display: block; animation: fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px);} to { opacity: 1; transform: translateY(0);} }
  `],
  imports: [RouterModule]
})
export class WelcomeComponent implements AfterViewInit {
  ngAfterViewInit(): void {
    // Initialize 3D Globe
    const container = document.getElementById('globe');
    if (container && typeof THREE !== 'undefined') {
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
      const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      container.appendChild(renderer.domElement);

      // Main sphere with wireframe
      const geometry = new THREE.SphereGeometry(5, 32, 32);
      const material = new THREE.MeshBasicMaterial({ 
        color: 0x2E8B57, 
        wireframe: true, 
        transparent: true, 
        opacity: 0.3 
      });
      const sphere = new THREE.Mesh(geometry, material);
      scene.add(sphere);

      // Inner glow effect
      const innerGeometry = new THREE.SphereGeometry(4.8, 32, 32);
      const innerMaterial = new THREE.MeshBasicMaterial({ 
        color: 0x009879, 
        transparent: true, 
        opacity: 0.15 
      });
      const innerSphere = new THREE.Mesh(innerGeometry, innerMaterial);
      scene.add(innerSphere);

      // Outer glow ring
      const ringGeometry = new THREE.RingGeometry(5.2, 5.5, 32);
      const ringMaterial = new THREE.MeshBasicMaterial({ 
        color: 0xF5A623, 
        transparent: true, 
        opacity: 0.1,
        side: THREE.DoubleSide
      });
      const ring = new THREE.Mesh(ringGeometry, ringMaterial);
      ring.rotation.x = Math.PI / 2;
      scene.add(ring);

      // Enhanced particle system
      const particleGeometry = new THREE.BufferGeometry();
      const particleCount = 100;
      const positions = new Float32Array(particleCount * 3);
      const colors = new Float32Array(particleCount * 3);
      
      for (let i = 0; i < particleCount * 3; i += 3) {
        // Create particles in a sphere around the globe
        const radius = 6 + Math.random() * 4;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.random() * Math.PI;
        
        positions[i] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i + 2] = radius * Math.cos(phi);
        
        // Color variation
        const colorChoice = Math.random();
        if (colorChoice < 0.4) {
          colors[i] = 0.18; colors[i + 1] = 0.55; colors[i + 2] = 0.34; // Sea Green
        } else if (colorChoice < 0.7) {
          colors[i] = 0.0; colors[i + 1] = 0.6; colors[i + 2] = 0.47; // Teal
        } else {
          colors[i] = 0.96; colors[i + 1] = 0.65; colors[i + 2] = 0.14; // Golden Orange
        }
      }
      
      particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      
      const particleMaterial = new THREE.PointsMaterial({
        size: 0.15,
        transparent: true,
        opacity: 0.8,
        vertexColors: true,
        blending: THREE.AdditiveBlending
      });
      
      const particles = new THREE.Points(particleGeometry, particleMaterial);
      scene.add(particles);
      
      // Position camera
      camera.position.z = 8;
      camera.position.y = 2;

      // Animation variables
      let time = 0;
      
      const animate = () => {
        requestAnimationFrame(animate);
        time += 0.01;
        
        // Main sphere rotation
        sphere.rotation.x += 0.001;
        sphere.rotation.y += 0.002;
        
        // Inner sphere counter-rotation
        innerSphere.rotation.x -= 0.0005;
        innerSphere.rotation.y -= 0.001;
        
        // Ring rotation
        ring.rotation.z += 0.003;
        
        // Particle system rotation and pulsing
        particles.rotation.x += 0.0005;
        particles.rotation.y += 0.001;
        particles.rotation.z += 0.0003;
        
        // Add subtle camera movement
        camera.position.x = Math.sin(time * 0.1) * 0.5;
        camera.position.y = 2 + Math.sin(time * 0.15) * 0.3;
        camera.lookAt(0, 0, 0);
        
        // Pulsing effect for particles
        const scale = 1 + Math.sin(time * 2) * 0.1;
        particles.scale.set(scale, scale, scale);
        
        renderer.render(scene, camera);
      };
      window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
      });
      animate();
    }

    // GSAP animations
    if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
      gsap.registerPlugin(ScrollTrigger);
      const cards = Array.from(document.querySelectorAll('.card-hover'));
      cards.forEach((card) => {
        gsap.from(card, {
          scrollTrigger: { trigger: card as Element, start: 'top 80%', toggleActions: 'play none none none' },
          y: 50,
          opacity: 0,
          duration: 1,
          ease: 'power3.out'
        });
      });
      const icons = Array.from(document.querySelectorAll('.feature-icon'));
      icons.forEach((icon) => {
        gsap.from(icon, {
          scrollTrigger: { trigger: icon as Element, start: 'top 80%', toggleActions: 'play none none none' },
          rotationY: 180,
          opacity: 0,
          duration: 1,
          ease: 'back.out(1.7)'
        });
      });
    }
  }
}


