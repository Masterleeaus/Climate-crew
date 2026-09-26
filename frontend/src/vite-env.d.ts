/// <reference types="vite/client" />

declare module 'leaflet/dist/images/*.png' {
    const value: string;
    export default value;
}
