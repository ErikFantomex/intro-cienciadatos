import { Body, Controller, Get, Post, Query } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { Auth } from '../auth/decorators';
import { IngestCryptoDto } from './dto/ingest-crypto.dto';
import { MarketQueryDto } from './dto/market-query.dto';
import { CryptoService } from './crypto.service';

@ApiTags('CryptoInsight')
@Controller('crypto')
export class CryptoController {
  constructor(private readonly cryptoService: CryptoService) {}

  @Get('health')
  health() {
    return this.cryptoService.health();
  }

  @Get('coins')
  coins() {
    return this.cryptoService.coins();
  }

  @Get('market-data')
  marketData(@Query() query: MarketQueryDto) {
    return this.cryptoService.marketData(query);
  }

  @Get('market-summary')
  marketSummary(@Query() query: MarketQueryDto) {
    return this.cryptoService.marketSummary(query);
  }

  @Post('ingest')
  @Auth()
  @ApiBearerAuth()
  ingest(@Body() body: IngestCryptoDto) {
    return this.cryptoService.ingest(body);
  }

  @Get('ingestion-runs')
  ingestionRuns(@Query('limit') limit?: string) {
    const parsedLimit = limit === undefined ? undefined : Number.parseInt(limit, 10);
    return this.cryptoService.ingestionRuns(parsedLimit);
  }
}
