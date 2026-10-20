import { HttpModule } from '@nestjs/axios';
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { CryptoController } from './crypto.controller';
import { CryptoService } from './crypto.service';
import { AuthModule } from '../auth/auth.module';

@Module({
  imports: [ConfigModule, HttpModule.register({ timeout: 20000 }), AuthModule],
  controllers: [CryptoController],
  providers: [CryptoService],
})
export class CryptoModule {}
