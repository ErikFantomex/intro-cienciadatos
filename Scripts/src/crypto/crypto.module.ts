import { HttpModule } from '@nestjs/axios';
import { Module } from '@nestjs/common';
import { CryptoController } from './crypto.controller';
import { CryptoService } from './crypto.service';

@Module({
  imports: [HttpModule.register({ timeout: 20000 })],
  controllers: [CryptoController],
  providers: [CryptoService],
})
export class CryptoModule {}
