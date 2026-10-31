pragma solidity 0.5.12;

contract Wallet1598 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return reserve; }
}
