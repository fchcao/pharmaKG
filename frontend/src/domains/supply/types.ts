// Supply Chain Domain specific types

export interface Manufacturer {
  id: string;
  name: string;
  location?: string;
  type?: string;
  status?: string;
  facilities?: Facility[];
  products?: Product[];
}

export interface Facility {
  id: string;
  name: string;
  manufacturerId: string;
  location: string;
  facilityType: string;
  capacity?: number;
  status?: string;
  certifications?: string[];
}

export interface Supplier {
  id: string;
  name: string;
  location?: string;
  supplierType: string;
  status?: string;
  products?: Product[];
}

export interface Product {
  id: string;
  name: string;
  manufacturerId?: string;
  supplierId?: string;
  category: string;
  dosageForm?: string;
  strength?: string;
  status?: string;
}

export interface Shortage {
  id: string;
  productId: string;
  productName: string;
  startDate: string;
  endDate?: string;
  reason?: string;
  status: string;
  severity?: 'low' | 'medium' | 'high';
}
