import {
  BadGatewayException,
  BadRequestException,
  ForbiddenException,
  Injectable,
  InternalServerErrorException,
  Logger,
  NotFoundException,
  ServiceUnavailableException,
  TooManyRequestsException,
  UnauthorizedException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { HttpService } from '@nestjs/axios';
import { AxiosError, AxiosRequestConfig } from 'axios';
import { firstValueFrom } from 'rxjs';
import { IngestCryptoDto } from './dto/ingest-crypto.dto';
import { MarketQueryDto } from './dto/market-query.dto';

@Injectable()
export class CryptoService {
  private readonly logger = new Logger(CryptoService.name);

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {}

  health() {
    return this.get('/health');
  }

  coins() {
    return this.get('/api/coins');
  }

  marketData(query: MarketQueryDto) {
    return this.get('/api/market-data', query);
  }

  marketSummary(query: MarketQueryDto) {
    return this.get('/api/market-summary', query);
  }

  ingest(body: IngestCryptoDto) {
    return this.request('/api/ingest', 'POST', undefined, body);
  }

  ingestionRuns(limit?: number) {
    return this.get('/api/ingestion-runs', limit === undefined ? undefined : { limit });
  }

  private get(path: string, params?: object) {
    return this.request(path, 'GET', params);
  }

  private async request(
    path: string,
    method: 'GET' | 'POST',
    params?: object,
    data?: object,
  ): Promise<unknown> {
    const baseUrl = this.configService.get<string>('CRYPTO_API_URL');
    const apiKey = this.configService.get<string>('CRYPTO_INTERNAL_API_KEY');
    if (!baseUrl || !apiKey) {
      throw new ServiceUnavailableException('La integración financiera no está configurada.');
    }

    const config: AxiosRequestConfig = {
      method,
      url: `${baseUrl.replace(/\/+$/, '')}${path}`,
      params,
      data,
      headers: { 'X-Internal-API-Key': apiKey },
      timeout: 20000,
    };

    try {
      const response = await firstValueFrom(this.httpService.request(config));
      return response.data;
    } catch (error) {
      this.logger.warn(`Servicio financiero no disponible al consultar ${path}.`);
      throw this.mapError(error);
    }
  }

  private mapError(error: unknown): Error {
    const status = (error as AxiosError).response?.status;
    switch (status) {
      case 400:
        return new BadRequestException('La solicitud financiera no es válida.');
      case 401:
        return new UnauthorizedException('La solicitud no está autenticada.');
      case 403:
        return new ForbiddenException('No tienes permiso para esta operación.');
      case 404:
        return new NotFoundException('No se encontró la información solicitada.');
      case 429:
        return new TooManyRequestsException('CoinGecko limitó las solicitudes. Inténtalo más tarde.');
      case 502:
        return new BadGatewayException('El proveedor devolvió una respuesta inválida.');
      case 503:
        return new ServiceUnavailableException('El servicio financiero o MySQL no está disponible.');
      default:
        if (status && status >= 500) {
          return new BadGatewayException('El servicio financiero no pudo completar la solicitud.');
        }
        if (status) {
          return new InternalServerErrorException('No se pudo procesar la solicitud financiera.');
        }
        return new ServiceUnavailableException('FastAPI no está disponible.');
    }
  }
}
