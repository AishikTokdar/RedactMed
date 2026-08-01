#!/usr/bin/env node
/**
 * CDK application entry point for RedactMed Platform.
 * Defines infrastructure stack and applies project tags.
 */
import * as dotenv from 'dotenv';
dotenv.config();

import * as cdk from 'aws-cdk-lib';
import { RedactMedStack } from '../lib/redactmed-stack';

const app = new cdk.App();
new RedactMedStack(app, 'RedactMedStack');

cdk.Tags.of(app).add('Project', 'RedactMed');
cdk.Tags.of(app).add('Purpose', process.env.PURPOSE || 'Demo');
cdk.Tags.of(app).add('Owner', process.env.OWNER_NAME || 'CDK');
