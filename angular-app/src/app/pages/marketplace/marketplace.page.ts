import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-marketplace',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="marketplace-container">
      <div class="header">
        <h1>Marketplace</h1>
        <div class="search-bar">
          <input type="text" placeholder="Search products..." [formControl]="searchControl">
          <button class="search-btn">Search</button>
        </div>
      </div>
      
      <div class="categories">
        <button class="category-btn" 
                *ngFor="let category of categories" 
                [class.active]="selectedCategory === category.id"
                (click)="selectCategory(category.id)">
          {{ category.name }}
        </button>
      </div>
      
      <div class="products-grid">
        <div class="product-card" *ngFor="let product of filteredProducts">
          <div class="product-image">
            <img [src]="product.image" [alt]="product.name">
          </div>
          <div class="product-info">
            <h3>{{ product.name }}</h3>
            <p class="description">{{ product.description }}</p>
            <p class="price">R{{ product.price }}</p>
            <p class="seller">by {{ product.seller }}</p>
          </div>
          <div class="product-actions">
            <button class="btn-primary" (click)="buy(product.id)">Buy Now</button>
            <button class="btn-secondary" (click)="addToCart(product.id)">Add to Cart</button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .marketplace-container { padding: 2rem; }
    .header { margin-bottom: 2rem; }
    .header h1 { color: #fff; margin-bottom: 1rem; }
    .search-bar { display: flex; gap: 0.5rem; }
    .search-bar input { flex: 1; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; padding: 0.75rem; border-radius: 0.5rem; }
    .search-btn { background: var(--primary-color); color: white; border: none; padding: 0.75rem 1rem; border-radius: 0.5rem; cursor: pointer; }
    .categories { display: flex; gap: 0.5rem; margin-bottom: 2rem; flex-wrap: wrap; }
    .category-btn { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.8); border: 1px solid rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer; }
    .category-btn.active, .category-btn:hover { background: var(--primary-color); color: white; border-color: var(--primary-color); }
    .products-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
    .product-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 1rem; padding: 1.5rem; }
    .product-image img { width: 100%; height: 200px; object-fit: cover; border-radius: 0.5rem; margin-bottom: 1rem; }
    .product-info h3 { color: #fff; margin-bottom: 0.5rem; }
    .description { color: rgba(255,255,255,0.7); margin-bottom: 0.5rem; }
    .price { color: var(--primary-color); font-weight: 700; font-size: 1.25rem; margin-bottom: 0.5rem; }
    .seller { color: rgba(255,255,255,0.6); font-size: 0.875rem; margin-bottom: 1rem; }
    .product-actions { display: flex; gap: 0.5rem; }
    .btn-primary { background: var(--primary-color); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; flex: 1; }
    .btn-secondary { background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; flex: 1; }
  `]
})
export class MarketplacePage {
  searchControl = new FormControl('');
  selectedCategory = 'all';
  
  categories = [
    { id: 'all', name: 'All' },
    { id: 'electronics', name: 'Electronics' },
    { id: 'clothing', name: 'Clothing' },
    { id: 'home', name: 'Home & Garden' },
    { id: 'books', name: 'Books' }
  ];
  
  products = [
    {
      id: 1,
      name: 'Smartphone',
      description: 'Latest smartphone with great features',
      price: 2500,
      seller: 'TechStore',
      image: 'assets/phone.jpg',
      category: 'electronics'
    },
    {
      id: 2,
      name: 'T-Shirt',
      description: 'Comfortable cotton t-shirt',
      price: 150,
      seller: 'FashionHub',
      image: 'assets/tshirt.jpg',
      category: 'clothing'
    }
  ];
  
  constructor(private api: ApiService) {
    this.searchControl.valueChanges.subscribe(value => {
      this.searchTerm = value || '';
    });
  }

  buy(productId: number) {
    this.api.addToCart(productId);
    const result = this.api.checkout();
    alert(result.message);
  }

  addToCart(productId: number) {
    this.api.addToCart(productId);
    alert('Added to cart');
  }
  
  get searchTerm(): string {
    return this.searchControl.value || '';
  }
  
  set searchTerm(value: string) {
    this.searchControl.setValue(value);
  }
  
  get filteredProducts() {
    let filtered = this.products;
    
    if (this.selectedCategory !== 'all') {
      filtered = filtered.filter(p => p.category === this.selectedCategory);
    }
    
    if (this.searchTerm) {
      filtered = filtered.filter(p => 
        p.name.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        p.description.toLowerCase().includes(this.searchTerm.toLowerCase())
      );
    }
    
    return filtered;
  }
  
  selectCategory(categoryId: string) {
    this.selectedCategory = categoryId;
  }
} 