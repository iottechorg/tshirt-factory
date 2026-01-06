export interface TshirtOptions {
  material: string;
  size: string;
  color: string;
  collar: string; // Changed facet to collar
}

export interface OrderPayload {
  //tshirtOptions: TshirtOptions;
 // aiGeneratedImage: string;
  product_name:string;
  product_details?:any;
}

export interface AiImageResponse {
  imageUrl: string;
}