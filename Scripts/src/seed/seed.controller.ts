import { Controller, NotFoundException, Post } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { ConfigService } from '@nestjs/config';

import { ValidRoles } from '../auth/interfaces';
import { Auth } from '../auth/decorators';

import { SeedService } from './seed.service';

@ApiTags('Seed')
@Controller('seed')
export class SeedController {
  constructor(
    private readonly seedService: SeedService,
    private readonly configService: ConfigService,
  ) {}

  @Post()
  @Auth(ValidRoles.admin)
  executeSeed() {
    if (
      this.configService.get<string>('NODE_ENV') === 'production' ||
      this.configService.get<string>('ENABLE_SEED_ENDPOINT') !== 'true'
    ) {
      throw new NotFoundException('La carga inicial no está habilitada.');
    }
    return this.seedService.runSeed()
  }
}
