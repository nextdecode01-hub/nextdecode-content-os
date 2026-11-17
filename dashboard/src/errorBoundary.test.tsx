import {describe,expect,it,vi} from 'vitest';
import type {ReactNode} from 'react';
import {render,screen} from '@testing-library/react';
import {ErrorBoundary} from './components';

function BrokenView():ReactNode{throw new Error('render failed');}

describe('Dashboard ErrorBoundary',()=>{
  it('contains a route render exception and offers recovery',()=>{
    const log=vi.spyOn(console,'error').mockImplementation(()=>{});
    render(<ErrorBoundary><BrokenView/></ErrorBoundary>);
    expect(screen.getByText('This dashboard view could not be displayed')).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Reload dashboard'})).toBeInTheDocument();
    log.mockRestore();
  });
});
