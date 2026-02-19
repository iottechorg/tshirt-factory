export interface ProductOptions {
  description: string;
  quantity: number;
}

export interface OrderPayload {
  product_name: string;
  product_details: any;
  quantity: number;
}

export interface AiImageResponse {
  imageUrl: string;
}